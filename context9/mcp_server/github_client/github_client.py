"""
GitHub API Client for reading files from GitHub repositories.

This module handles communication with GitHub REST API to fetch file contents.
Uses local caching with periodic synchronization to reduce API calls.
"""

import subprocess
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loguru import logger
from starlette.responses import JSONResponse
from starlette import status
from starlette.requests import Request
import random
from ..markdown import rewrite_relative_paths


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
        repos: List[Dict[str, Any]],
        token: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        cache_dir: Optional[str] = None,
        sync_interval: int = 600,
        enable_github_webhook: bool = False,
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
        """
        self.token = token
        self.timeout = timeout
        self.sync_interval = sync_interval
        self.enable_github_webhook = enable_github_webhook

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

        logger.info(f"repos: {repos}")
        self.repos = repos
        for repo in self.repos:
            repo["sync_timer"] = None
            repo["is_syncing"] = False
            repo["sync_lock"] = threading.Lock()

        # Create session with retry strategy (still needed for initial clone)
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

        # Set up authentication headers
        self.headers = {
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "Context9/0.1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

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
        if self.token:
            # Use token in URL for authentication
            return f"https://{self.token}@github.com/{repo['owner']}/{repo['repo']}.git"
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

        with repo["sync_lock"]:
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
        Sync repositories from remote to local cache.
        Uses git clone if repository doesn't exist, or git pull if it does.
        """
        for repo in self.repos:
            self._sync_repository(repo)

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

    def get_doc_list(self) -> List[Dict[str, Any]]:
        """Get the list of documentation files."""
        results = []
        for repo in self.repos:
            results.append(
                {
                    "repo_name": repo["repo"],
                    "repo_description": repo["desc"],
                    "repo_spec_path": f"remotedoc://{repo['owner']}/{repo['repo']}/{repo['branch']}/{repo['root_spec_path']}",
                }
            )
        logger.info(f"Doc list: {results}")
        return results

    def read_file(self, path: str, branch: Optional[str] = None) -> str:
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

        # Use sync lock to prevent race conditions with _sync_repository
        # This ensures file reads don't happen during git operations (git reset --hard)
        with repo["sync_lock"]:
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

    def check_rate_limit(self) -> dict:
        """
        Check current GitHub API rate limit status.

        Returns:
            Dictionary with rate limit information
        """
        url = f"{self.BASE_URL}/rate_limit"

        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to check rate limit: {response.status_code}")
                return {}
        except Exception as e:
            logger.warning(f"Error checking rate limit: {e}")
            return {}

    def _fetch_repo_description(self, repo: Dict[str, Any]) -> Optional[str]:
        """
        Fetch repository description from GitHub API for a single repository.

        Args:
            repo: Repository dictionary containing 'owner' and 'repo' keys

        Returns:
            Repository description string, or None if not available or on error
        """
        url = f"{self.BASE_URL}/repos/{repo['owner']}/{repo['repo']}"

        try:
            response = self.session.get(url, headers=self.headers, timeout=self.timeout)

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
