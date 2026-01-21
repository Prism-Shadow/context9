"""
GitHub API Client for reading files from GitHub repositories.

This module handles communication with GitHub REST API to fetch file contents.
Uses local caching with periodic synchronization to reduce API calls.
"""

import hashlib
import shutil
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger
from .rw_lock import ReadWriteLock, ReadLockContext, WriteLockContext
from starlette.responses import JSONResponse
from starlette import status
from starlette.requests import Request
import random
from ...markdown import rewrite_relative_paths
from ....database.database import SessionLocal
from ....database.models import ApiKey, ApiKeyRepository, Repository

from dotenv import load_dotenv
import os


class GitHubClientError(Exception):
    """Base exception for GitHub client errors."""

    pass


class GitHubFileNotFoundError(GitHubClientError):
    """Raised when a file is not found in the repository."""

    pass


class GitHubAuthenticationError(GitHubClientError):
    """Raised when authentication fails."""

    pass


class GitHubRateLimitError(GitHubClientError):
    """Raised when GitHub API rate limit is exceeded."""

    pass


class GitHubClient:
    """
    Client for interacting with GitHub REST API to read files.
    """

    BASE_URL = "https://api.github.com"

    def __init__(
        self,
        repos: Optional[List[Dict[str, Any]]] = None,
        timeout: int = 30,
        max_retries: int = 3,
        cache_dir: Optional[str] = None,
        sync_interval: int = 600,
        enable_github_webhook: bool = False,
        max_workers: int = 5,
    ):
        """
        Initialize GitHub client.

        Args:
            repos: List of repositories to sync
            token: GitHub personal access token (optional, but recommended)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            cache_dir: Directory to cache repositories locally (default: ~/.github_cache)
            sync_interval: Interval in seconds to sync repository (default: 600 = 10 minutes)
            enable_github_webhook: Enable GitHub webhook (default: False)
            max_workers: Maximum number of workers to use for parallel synchronization (default: 5)
        """
        self.timeout = timeout
        self.sync_interval = sync_interval
        self.enable_github_webhook = enable_github_webhook
        self.max_workers = max_workers

        if self.enable_github_webhook and self.sync_interval is not None:
            raise ValueError(
                "sync_interval must be None when enable_github_webhook is True"
            )

        # Set up local cache directory
        if cache_dir is None:
            self.cache_dir = Path.cwd() / ".github_cache"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create session with retry strategy (must be initialized before _sync_database)
        # as _sync_database may trigger methods that need self.session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.repos = []

        if repos is None:
            logger.warning(
                "repos parameter is not provided. Repositories will be loaded from database."
            )
            self._sync_database()
            self.use_database = True
        else:
            logger.warning(
                "repos parameter is provided. Repositories will be loaded from the parameter."
            )
            load_dotenv()
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token is None:
                raise ValueError("GITHUB_TOKEN is not set in the environment variables")
            for repo in repos:
                repo["github_token"] = github_token
            self.repos = repos
            self.use_database = False

    def _sync_database(self):
        # Load repositories from database instead of using repos parameter
        # Note: repos parameter is kept for backward compatibility but not used
        logger.warning(
            "repos parameter is provided but will be ignored. Repositories will be loaded from database."
        )

        # Load repositories from database
        db = SessionLocal()
        try:
            db_repos = db.query(Repository).all()
            self.repos = []
            for db_repo in db_repos:
                repo_dict = {
                    "owner": db_repo.owner,
                    "repo": db_repo.repo,
                    "branch": db_repo.branch,
                    "root_spec_path": db_repo.root_spec_path or "spec.md",
                    "github_token": db_repo.github_token,
                    "sync_timer": None,
                    "is_syncing": False,
                    "sync_lock": ReadWriteLock(),
                    "desc": None,
                }
                self.repos.append(repo_dict)
            logger.info(f"Loaded {len(self.repos)} repositories from database")
            if self.repos:
                logger.debug(
                    f"Repositories: {[(r['owner'], r['repo'], r['branch']) for r in self.repos]}"
                )
        except Exception as e:
            logger.error(
                f"Failed to load repositories from database: {e}", exc_info=True
            )
            # Fallback to empty list if database read fails
            self.repos = []
        finally:
            db.close()

        # Initial sync (non-blocking, will retry in background if fails)
        logger.info(f"Initializing local cache at: {self.cache_dir}")
        try:
            self._sync_repositories()
        except Exception as e:
            logger.warning(f"Initial sync failed, will retry in background: {e}")
            # Repository might not be available yet, but we'll retry in the timer

        if self.sync_interval is not None:
            # Start periodic sync timer
            self._start_sync_timer()

    def _get_repo_url(self, repo: Dict[str, Any]) -> str:
        """Get the repository URL for git operations."""
        token = repo.get("github_token")
        if token:
            # Use token in URL for authentication
            return f"https://{token}@github.com/{repo['owner']}/{repo['repo']}.git"
        else:
            return f"https://github.com/{repo['owner']}/{repo['repo']}.git"

    def _sync_repository(self, repo: Dict[str, Any]):
        """
        Sync repository from remote to local cache.
        Uses git clone if repository doesn't exist, or git pull if it does.
        """
        if repo["is_syncing"]:
            logger.debug("Sync already in progress, skipping...")
            return

        with WriteLockContext(repo["sync_lock"]):
            repo["is_syncing"] = True
            try:
                repo_url = self._get_repo_url(repo)

                repo_dir = (
                    self.cache_dir / repo["owner"] / repo["repo"] / repo["branch"]
                )

                if not repo_dir.exists() or not (repo_dir / ".git").exists():
                    # clone repository
                    logger.info(
                        f"Cloning repository {repo['owner']}/{repo['repo']}/{repo['branch']} to {repo_dir}"
                    )
                    try:
                        subprocess.run(
                            [
                                "git",
                                "clone",
                                "--branch",
                                repo["branch"],
                                "--single-branch",
                                "--depth",
                                "1",
                                repo_url,
                                str(repo_dir),
                            ],
                            check=True,
                            capture_output=True,
                            timeout=self.timeout * 2,
                        )
                        logger.info(f"Successfully cloned repository to {repo_dir}")
                    except subprocess.CalledProcessError as e:
                        error_output = ""
                        if e.stderr:
                            try:
                                error_output = e.stderr.decode(
                                    "utf-8", errors="replace"
                                )
                            except:
                                error_output = str(e.stderr)

                        # If clone fails, try without token in URL (for public repos)
                        if self.token:
                            logger.warning(
                                f"Clone with token failed: {error_output}. Trying without token..."
                            )
                            public_url = (
                                f"https://github.com/{repo['owner']}/{repo['repo']}.git"
                            )
                            try:
                                subprocess.run(
                                    [
                                        "git",
                                        "clone",
                                        "--branch",
                                        repo["branch"],
                                        "--single-branch",
                                        "--depth",
                                        "1",
                                        public_url,
                                        str(repo_dir),
                                    ],
                                    check=True,
                                    capture_output=True,
                                    timeout=self.timeout * 2,
                                )
                                logger.info(
                                    f"Successfully cloned repository {repo['owner']}/{repo['repo']}/{repo['branch']} without token to {repo_dir}"
                                )
                            except subprocess.CalledProcessError as e2:
                                error_output2 = ""
                                if e2.stderr:
                                    try:
                                        error_output2 = e2.stderr.decode(
                                            "utf-8", errors="replace"
                                        )
                                    except:
                                        error_output2 = str(e2.stderr)
                                logger.error(
                                    f"Clone failed even without token: {error_output2} for repository {repo['owner']}/{repo['repo']}/{repo['branch']}"
                                )
                                raise GitHubClientError(
                                    f"Failed to clone repository {repo['owner']}/{repo['repo']}/{repo['branch']}: {error_output2}"
                                )
                        else:
                            logger.error(
                                f"Clone failed: {error_output} for repository {repo['owner']}/{repo['repo']}/{repo['branch']}"
                            )
                            raise GitHubClientError(
                                f"Failed to clone repository {repo['owner']}/{repo['repo']}/{repo['branch']}: {error_output}"
                            )
                else:
                    # Update existing repository
                    logger.info(
                        f"Updating repository {repo['owner']}/{repo['repo']}/{repo['branch']} from remote to {repo_dir}"
                    )
                    try:
                        # Fetch and checkout the branch
                        subprocess.run(
                            ["git", "fetch", "origin", repo["branch"]],
                            cwd=str(repo_dir),
                            check=True,
                            capture_output=True,
                            timeout=self.timeout * 2,
                        )
                        subprocess.run(
                            ["git", "checkout", repo["branch"]],
                            cwd=str(repo_dir),
                            check=True,
                            capture_output=True,
                            timeout=self.timeout,
                        )
                        subprocess.run(
                            ["git", "reset", "--hard", f"origin/{repo['branch']}"],
                            cwd=str(repo_dir),
                            check=True,
                            capture_output=True,
                            timeout=self.timeout,
                        )
                        logger.info(
                            f"Successfully updated repository {repo['owner']}/{repo['repo']}/{repo['branch']} at {repo_dir}"
                        )
                    except subprocess.CalledProcessError as e:
                        logger.error(
                            f"Failed to update repository {repo['owner']}/{repo['repo']}/{repo['branch']}: {e}"
                        )
                        if e.stdout:
                            logger.error(f"stdout: {e.stdout.decode()}")
                        if e.stderr:
                            logger.error(f"stderr: {e.stderr.decode()}")
                        raise GitHubClientError(
                            f"Failed to sync repository {repo['owner']}/{repo['repo']}/{repo['branch']}: {e}"
                        )
                    except subprocess.TimeoutExpired:
                        logger.error("Repository sync timed out")
                        raise GitHubClientError(
                            f"Repository sync timed out {repo['owner']}/{repo['repo']}/{repo['branch']}"
                        )
                repo["desc"] = self._fetch_repo_description(repo)
                if repo["desc"] is None:
                    repo["desc"] = ""
            except Exception as e:
                logger.error(f"Error syncing repository: {e}", exc_info=True)
                raise
            finally:
                repo["is_syncing"] = False

    def _sync_repositories(self):
        """
        Sync repositories from remote to local cache in parallel.
        Uses git clone if repository doesn't exist, or git pull if it does.
        Maximum concurrency is set to 5.
        """
        start_time = time.time()
        repo_count = len(self.repos)
        logger.info(
            f"Starting to sync {repo_count} repositories in parallel (max workers: 5)"
        )

        max_workers = self.max_workers
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all sync tasks
            future_to_repo = {
                executor.submit(self._sync_repository, repo): repo
                for repo in self.repos
            }

            # Wait for all tasks to complete and handle results
            for future in as_completed(future_to_repo):
                repo = future_to_repo[future]
                try:
                    future.result()
                    logger.info(
                        f"Successfully synced repository {repo['owner']}/{repo['repo']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Error syncing repository {repo['owner']}/{repo['repo']}: {e}",
                        exc_info=True,
                    )

        elapsed_time = time.time() - start_time
        logger.info(
            f"Completed syncing {repo_count} repositories in {elapsed_time:.2f} seconds"
        )

    def _start_sync_timer(self):
        """
        Start the periodic sync timer.
        Randomly select interval for each repository to avoid rate limit of GitHub API.
        """

        def sync_and_reschedule(repo: Dict[str, Any]):
            try:
                self._sync_repository(repo)
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
            finally:
                # Reschedule the timer
                cur_inverval = self._get_random_interval()
                repo["sync_timer"] = threading.Timer(
                    cur_inverval, sync_and_reschedule, args=(repo,)
                )
                repo["sync_timer"].daemon = True
                repo["sync_timer"].start()
                logger.info(
                    f"Rescheduled periodic sync timer for repository {repo['owner']}/{repo['repo']} (interval: {cur_inverval}s)"
                )

        for repo in self.repos:
            cur_inverval = self._get_random_interval()
            repo["sync_timer"] = threading.Timer(
                cur_inverval, sync_and_reschedule, args=(repo,)
            )
            repo["sync_timer"].daemon = True
            repo["sync_timer"].start()
            logger.info(
                f"Started periodic sync timer for repository {repo['owner']}/{repo['repo']} (interval: {cur_inverval}s)"
            )

    def _get_random_interval(self) -> int:
        """Get a random interval between -0.3 and 0.3 of the sync_interval."""
        factor = random.uniform(-0.3, 0.3)
        return self.sync_interval * (1 + factor)

    def stop_sync_timer(self):
        """Stop the periodic sync timer."""
        for repo in self.repos:
            if repo["sync_timer"]:
                repo["sync_timer"].cancel()
                repo["sync_timer"] = None
                logger.info(
                    f"Stopped periodic sync timer for repository {repo['owner']}/{repo['repo']}"
                )

    def add_repository(
        self, owner: str, repo: str, branch: str, root_spec_path: str = "spec.md"
    ):
        """
        Add a new repository to the client and start syncing it.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            root_spec_path: Root spec path (default: "spec.md")
        """
        # Check if repository already exists
        for existing_repo in self.repos:
            if (
                existing_repo["owner"] == owner
                and existing_repo["repo"] == repo
                and existing_repo["branch"] == branch
            ):
                logger.warning(
                    f"Repository {owner}/{repo}/{branch} already exists, updating instead"
                )
                self.update_repository(owner, repo, branch, root_spec_path)
                return

        # Create new repository dict
        new_repo = {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "root_spec_path": root_spec_path,
            "sync_timer": None,
            "is_syncing": False,
            "sync_lock": ReadWriteLock(),
            "desc": None,
        }

        # Add to repos list
        self.repos.append(new_repo)

        # Sync the repository
        try:
            self._sync_repository(new_repo)
            logger.info(f"Successfully added repository {owner}/{repo}/{branch}")
        except Exception as e:
            logger.error(
                f"Failed to sync newly added repository {owner}/{repo}/{branch}: {e}"
            )

        # Start sync timer if enabled
        if self.sync_interval is not None:
            self._start_sync_timer_for_repo(new_repo)

    def update_repository(
        self,
        owner: str,
        repo: str,
        branch: str,
        new_owner: Optional[str] = None,
        new_repo: Optional[str] = None,
        new_branch: Optional[str] = None,
        new_root_spec_path: Optional[str] = None,
    ):
        """
        Update an existing repository configuration.

        Args:
            owner: Current repository owner
            repo: Current repository name
            branch: Current branch name
            new_owner: New owner (optional)
            new_repo: New repository name (optional)
            new_branch: New branch name (optional)
            new_root_spec_path: New root spec path (optional)
        """
        # Find the repository
        repo_dict = None
        for r in self.repos:
            if r["owner"] == owner and r["repo"] == repo and r["branch"] == branch:
                repo_dict = r
                break

        if repo_dict is None:
            logger.warning(
                f"Repository {owner}/{repo}/{branch} not found, adding as new repository"
            )
            # If not found, add as new repository
            final_owner = new_owner if new_owner is not None else owner
            final_repo = new_repo if new_repo is not None else repo
            final_branch = new_branch if new_branch is not None else branch
            final_root_spec_path = (
                new_root_spec_path if new_root_spec_path is not None else "spec.md"
            )
            self.add_repository(
                final_owner, final_repo, final_branch, final_root_spec_path
            )
            return

        # Stop sync timer if it exists
        if repo_dict["sync_timer"]:
            repo_dict["sync_timer"].cancel()
            repo_dict["sync_timer"] = None

        # Update repository fields
        if new_owner is not None:
            repo_dict["owner"] = new_owner
        if new_repo is not None:
            repo_dict["repo"] = new_repo
        if new_branch is not None:
            repo_dict["branch"] = new_branch
        if new_root_spec_path is not None:
            repo_dict["root_spec_path"] = new_root_spec_path

        # Sync the repository with new configuration
        try:
            self._sync_repository(repo_dict)
            logger.info(
                f"Successfully updated repository {repo_dict['owner']}/{repo_dict['repo']}/{repo_dict['branch']}"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync updated repository {repo_dict['owner']}/{repo_dict['repo']}/{repo_dict['branch']}: {e}"
            )

        # Restart sync timer if enabled
        if self.sync_interval is not None:
            self._start_sync_timer_for_repo(repo_dict)

    def remove_repository(self, owner: str, repo: str, branch: str):
        """
        Remove a repository from the client and stop syncing it.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
        """
        # Find and remove the repository
        repo_to_remove = None
        for r in self.repos:
            if r["owner"] == owner and r["repo"] == repo and r["branch"] == branch:
                repo_to_remove = r
                break

        if repo_to_remove is None:
            logger.warning(f"Repository {owner}/{repo}/{branch} not found")
            return

        # Stop sync timer if it exists
        if repo_to_remove["sync_timer"]:
            repo_to_remove["sync_timer"].cancel()
            repo_to_remove["sync_timer"] = None

        # Remove from repos list
        self.repos.remove(repo_to_remove)

        # Remove local cache directory and empty parent dirs (repo, owner)
        repo_dir = (
            self.cache_dir
            / repo_to_remove["owner"]
            / repo_to_remove["repo"]
            / repo_to_remove["branch"]
        )
        if repo_dir.exists():
            try:
                shutil.rmtree(repo_dir)
                logger.info(f"Removed local cache directory: {repo_dir}")
                # Remove empty parent directories (repo, then owner)
                for parent in [repo_dir.parent, repo_dir.parent.parent]:
                    if parent != self.cache_dir and parent.exists():
                        try:
                            parent.rmdir()
                            logger.info(f"Removed empty directory: {parent}")
                        except OSError:
                            pass
            except Exception as e:
                logger.warning(
                    f"Failed to remove local cache directory {repo_dir}: {e}"
                )

        logger.info(f"Successfully removed repository {owner}/{repo}/{branch}")

    def _start_sync_timer_for_repo(self, repo: Dict[str, Any]):
        """
        Start the periodic sync timer for a specific repository.

        Args:
            repo: Repository dictionary
        """

        def sync_and_reschedule(repo: Dict[str, Any]):
            try:
                self._sync_repository(repo)
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
            finally:
                # Reschedule the timer
                cur_interval = self._get_random_interval()
                repo["sync_timer"] = threading.Timer(
                    cur_interval, sync_and_reschedule, args=(repo,)
                )
                repo["sync_timer"].daemon = True
                repo["sync_timer"].start()
                logger.info(
                    f"Rescheduled periodic sync timer for repository {repo['owner']}/{repo['repo']} (interval: {cur_interval}s)"
                )

        cur_interval = self._get_random_interval()
        repo["sync_timer"] = threading.Timer(
            cur_interval, sync_and_reschedule, args=(repo,)
        )
        repo["sync_timer"].daemon = True
        repo["sync_timer"].start()
        logger.info(
            f"Started periodic sync timer for repository {repo['owner']}/{repo['repo']} (interval: {cur_interval}s)"
        )

    def list_doc(self, api_key: str) -> List[Dict[str, Any]]:
        """Get the list of documentation files."""
        results = []
        if self.use_database:
            repos = self.list_accessible_repositories(api_key)
        else:
            repos = self.repos
        logger.debug(f"Accessible repositories: {repos}")
        for repo in repos:
            results.append(
                {
                    "repo_name": repo["repo"],
                    "repo_description": repo["desc"],
                    "repo_spec_path": f"remotedoc://{repo['owner']}/{repo['repo']}/{repo['branch']}/{repo['root_spec_path']}",
                }
            )
        logger.debug(f"Doc list: {results}")
        return results

    def list_accessible_repositories(self, api_key: str) -> List[Dict[str, Any]]:
        """
        List all repositories that the given Context9 API key has access to.

        Uses ApiKey -> ApiKeyRepository -> Repository to resolve which
        repositories are bound to this api_key.

        Args:
            api_key: Context9 API key (models.ApiKey, e.g. Bearer token value)

        Returns:
            List of dicts, each with: owner, repo, desc, branch, root_spec_path.
            desc comes from in-memory synced repo if available, else "".
            root_spec_path defaults to "spec.md" when not set.

        Raises:
            GitHubAuthenticationError: When api_key is not found (invalid)
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        db = SessionLocal()
        try:
            api_key_record = (
                db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()
            )
            if not api_key_record:
                raise GitHubAuthenticationError("Invalid or unknown API key")

            ak_repos = (
                db.query(ApiKeyRepository)
                .filter(ApiKeyRepository.api_key_id == api_key_record.id)
                .all()
            )
            repo_ids = [ar.repository_id for ar in ak_repos]
            repositories = (
                db.query(Repository).filter(Repository.id.in_(repo_ids)).all()
            )
        finally:
            db.close()

        def desc_for(owner: str, repo: str, branch: str) -> str:
            for r in self.repos:
                if r["owner"] == owner and r["repo"] == repo and r["branch"] == branch:
                    return r.get("desc") or ""
            return ""

        result: List[Dict[str, Any]] = []
        for r in repositories:
            result.append(
                {
                    "owner": r.owner,
                    "repo": r.repo,
                    "desc": desc_for(r.owner, r.repo, r.branch),
                    "branch": r.branch,
                    "root_spec_path": r.root_spec_path or "spec.md",
                }
            )
        logger.info(
            f"Listed {len(result)} repositories accessible by the given API key"
        )
        return result

    def can_access_repository(
        self, owner: str, repo: str, branch: str, api_key: str
    ) -> bool:
        """
        Check whether the given Context9 API key has access to the repository.

        Optimized version: Uses JOIN to combine 3 queries into 1 for better performance.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name
            api_key: Context9 API key (models.ApiKey, e.g. Bearer token value)

        Returns:
            True if the api_key is bound to a Repository with the given owner,
            repo, branch via ApiKeyRepository; False if api_key is invalid, the
            repository does not exist, or it is not linked to this api_key.
        """
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        db = SessionLocal()
        try:
            # Use JOIN to combine 3 queries into 1 for ~60-70% performance improvement
            result = (
                db.query(ApiKeyRepository)
                .join(ApiKey, ApiKeyRepository.api_key_id == ApiKey.id)
                .join(Repository, ApiKeyRepository.repository_id == Repository.id)
                .filter(
                    ApiKey.key_hash == key_hash,
                    Repository.owner == owner,
                    Repository.repo == repo,
                    Repository.branch == branch,
                )
                .first()
            )
            return result is not None
        finally:
            db.close()

    def read_doc(self, path: str, api_key: str, branch: Optional[str] = None) -> str:
        """
        Read a file from the local cached repository.

        Args:
            path: File path relative to repository root
            branch: Branch name (defaults to self.branch, must match cached branch)

        Returns:
            File contents as string

        Raises:
            GitHubFileNotFoundError: If file doesn't exist
            GitHubClientError: For other errors
        """

        def get_repo(path: str) -> str:
            """Get the repository name from the path."""
            repo_name = path.split("/")[1]
            for r in self.repos:
                if r["repo"] == repo_name:
                    return r
            return None

        repo = get_repo(path)
        if repo is None:
            raise GitHubClientError(f"Repository related to path {path} not found")

        branch = path.split("/")[2]

        # Verify branch matches cached branch
        if branch != repo["branch"]:
            logger.warning(
                f"Requested branch {branch} differs from cached branch {repo['branch']}. Using cached branch."
            )

        if self.use_database and not self.can_access_repository(
            repo["owner"], repo["repo"], branch, api_key
        ):
            raise GitHubAuthenticationError(
                f"API key does not have access to repository {repo['owner']}/{repo['repo']}/{branch}"
            )

        # Construct local file path
        local_file_path = self.cache_dir / path

        logger.info(f"Reading file from local cache: {local_file_path}")

        # If repository doesn't exist locally, sync first (outside lock to avoid deadlock)
        if not (self.cache_dir / path).exists():
            logger.warning("Local repository cache not found, attempting to sync...")
            try:
                self._sync_repository(repo)
            except Exception as e:
                logger.error(f"Failed to sync repository: {e}")
                error_msg = f"Repository cache not available and sync failed: {e}"
                raise GitHubClientError(error_msg)

        # Use read lock to allow concurrent reads while preventing race conditions with _sync_repository
        # Multiple readers can read simultaneously, but write operations (git reset --hard) require exclusive access
        with ReadLockContext(repo["sync_lock"]):
            try:
                # Check if file exists
                if not local_file_path.exists():
                    error_msg = f"File not found: {path} in {repo['owner']}/{repo['repo']} (local cache)"
                    logger.error(error_msg)
                    raise GitHubFileNotFoundError(error_msg)

                # Verify the file is within the repository directory (security check)
                try:
                    local_file_path.resolve().relative_to(
                        (self.cache_dir / path).resolve()
                    )
                except ValueError:
                    error_msg = f"Invalid path: {path} (path traversal attempt)"
                    logger.error(error_msg)
                    raise GitHubClientError(error_msg)

                # Read file content
                with open(local_file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                logger.info(
                    f"Successfully read file from local cache: {path} ({len(content)} characters)"
                )

                current_path = path.split("/", maxsplit=3)[3]
                logger.info(f"Current path: {current_path}")
                content = rewrite_relative_paths(
                    content, repo["owner"], repo["repo"], repo["branch"], current_path
                )
                logger.info("Successfully converted to Context9 remotedoc:// URLs")

                return content

            except GitHubFileNotFoundError:
                raise

            except UnicodeDecodeError:
                # Try reading as binary and decode with error handling
                try:
                    with open(local_file_path, "rb") as f:
                        content = f.read().decode("utf-8", errors="replace")
                    logger.warning(
                        f"File {path} had encoding issues, read with error handling"
                    )
                    return content
                except Exception as e:
                    error_msg = f"Failed to read file {path}: {e}"
                    logger.error(error_msg)
                    raise GitHubClientError(error_msg)

            except Exception as e:
                error_msg = f"Unexpected error while reading file {path}: {e}"
                logger.error(error_msg, exc_info=True)
                raise GitHubClientError(error_msg)

    def _fetch_repo_description(self, repo: Dict[str, Any]) -> Optional[str]:
        """
        Fetch repository description from GitHub API for a single repository.

        Args:
            repo: Repository dictionary containing 'owner' and 'repo' keys

        Returns:
            Repository description string, or None if not available or on error
        """
        url = f"{self.BASE_URL}/repos/{repo['owner']}/{repo['repo']}"
        headers = {
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "Context9/0.1.0",
        }
        if repo.get("github_token"):
            headers["Authorization"] = f"token {repo.get('github_token')}"

        try:
            response = self.session.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 200:
                repo_info = response.json()
                description = repo_info.get("description")
                logger.info(
                    f"Fetched description for {repo['owner']}/{repo['repo']}: {description}"
                )
                return description
            elif response.status_code == 404:
                logger.warning(f"Repository {repo['owner']}/{repo['repo']} not found")
                return None
            elif response.status_code == 403:
                logger.warning(
                    f"Access forbidden for {repo['owner']}/{repo['repo']} (may be private or rate limited)"
                )
                return None
            else:
                logger.warning(
                    f"Failed to fetch description for {repo['owner']}/{repo['repo']}: "
                    f"HTTP {response.status_code}"
                )
                return None
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error fetching description for {repo['owner']}/{repo['repo']}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error fetching description for {repo['owner']}/{repo['repo']}: {e}",
                exc_info=True,
            )
            return None

    async def handle_github_webhook(self, request: Request) -> JSONResponse:
        """
        Handle POST requests from GitHub webhooks.

        Args:
            request: The incoming Starlette request

        Returns:
            JSONResponse: Response indicating success or failure
        """
        try:
            # Get the event type from headers
            event_type = request.headers.get("X-GitHub-Event", "unknown")
            delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")

            logger.info(
                f"Received GitHub webhook: event={event_type}, delivery_id={delivery_id}"
            )

            # Parse the JSON payload
            payload: Dict[str, Any] = await request.json()

            logger.info(f"Payload: {payload}")

            # Log basic information about the event
            if event_type == "push":
                ref = payload.get("ref", "unknown")
                commits = payload.get("commits", [])
                logger.info(f"Push event: ref={ref}, commits_count={len(commits)}")
                logger.info("Syncing repository...")
                self._sync_repository()
                logger.info("Repository synced successfully")
            else:
                logger.info(
                    f"Event type: {event_type}, payload keys: {list(payload.keys())}"
                )

            # Here you can add your custom logic to handle the webhook
            # For example, update cache, trigger rebuilds, etc.

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": "success",
                    "event": event_type,
                    "delivery_id": delivery_id,
                    "message": "Webhook received successfully",
                },
            )

        except Exception as e:
            logger.error(f"Error processing GitHub webhook: {e}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "message": f"Failed to process webhook: {str(e)}",
                },
            )
