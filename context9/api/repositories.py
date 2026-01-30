"""Repository management routes."""

import requests
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from loguru import logger

from ..database import get_db
from ..database.models import Repository
from ..auth.admin_auth import get_current_admin
from ..utils.datetime_utils import (
    get_utc_now,
    convert_to_client_timezone,
    get_client_timezone,
)
from ..mcp_server import mcp_server

router = APIRouter()


class CreateRepositoryRequest(BaseModel):
    owner: str
    repo: str
    branch: str
    root_spec_path: str = "spec.md"
    github_token: Optional[str] = None


class UpdateRepositoryRequest(BaseModel):
    owner: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None
    root_spec_path: Optional[str] = None
    github_token: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: int
    owner: str
    repo: str
    branch: str
    root_spec_path: str
    has_github_token: bool = False
    github_token_created_at: Optional[str] = None
    github_token_updated_at: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class CreateRepositoryResponse(RepositoryResponse):
    github_token: Optional[str] = None


class SetGithubTokenRequest(BaseModel):
    github_token: str


class SetGithubTokenResponse(BaseModel):
    id: int
    github_token: str
    github_token_created_at: str
    github_token_updated_at: Optional[str] = None


class VerifyGithubTokenResponse(BaseModel):
    valid: bool
    scopes: Optional[List[str]] = None
    rate_limit_remaining: Optional[int] = None
    error: Optional[str] = None


class ExportRepositoryItem(BaseModel):
    owner: str
    repo: str
    branch: str
    root_spec_path: str
    github_token: Optional[str] = None


class ExportRepositoriesResponse(BaseModel):
    repositories: List[ExportRepositoryItem]


class ImportRepositoriesRequest(BaseModel):
    repositories: List[ExportRepositoryItem]


class ImportRepositoriesError(BaseModel):
    owner: str
    repo: str
    branch: str
    error: str


class ImportRepositoriesResponse(BaseModel):
    created: int = 0
    skipped: int = 0
    errors: List[ImportRepositoriesError] = []


@router.post(
    "/import",
    response_model=ImportRepositoriesResponse,
)
def import_repositories(
    request: ImportRepositoriesRequest,
    http_request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Import repositories from exported JSON (skips duplicates by owner/repo/branch)."""
    created = 0
    skipped = 0
    errors: List[ImportRepositoriesError] = []

    for item in request.repositories:
        existing = (
            db.query(Repository)
            .filter(
                Repository.owner == item.owner,
                Repository.repo == item.repo,
                Repository.branch == item.branch,
            )
            .first()
        )
        if existing:
            skipped += 1
            continue

        try:
            repo = Repository(
                owner=item.owner,
                repo=item.repo,
                branch=item.branch,
                root_spec_path=item.root_spec_path or "spec.md",
            )
            if item.github_token:
                repo.github_token = item.github_token
                repo.github_token_created_at = get_utc_now()
            db.add(repo)
            db.commit()
            db.refresh(repo)
            created += 1

            if mcp_server.github_client is not None:
                try:
                    mcp_server.github_client.add_repository(
                        owner=repo.owner,
                        repo=repo.repo,
                        branch=repo.branch,
                        root_spec_path=repo.root_spec_path,
                        github_token=repo.github_token,
                    )
                    logger.info(
                        f"Imported and synced repository {repo.owner}/{repo.repo}/{repo.branch}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to sync imported repository {repo.owner}/{repo.repo}/{repo.branch}: {e}",
                        exc_info=True,
                    )
        except Exception as e:
            db.rollback()
            errors.append(
                ImportRepositoriesError(
                    owner=item.owner,
                    repo=item.repo,
                    branch=item.branch,
                    error=str(e),
                )
            )

    return ImportRepositoriesResponse(created=created, skipped=skipped, errors=errors)


@router.get(
    "/export",
    response_model=ExportRepositoriesResponse,
    response_model_exclude_none=True,
)
def export_repositories(
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Export all repositories with config (including github_token when set) for backup."""
    repos = db.query(Repository).all()
    items = [
        ExportRepositoryItem(
            owner=repo.owner,
            repo=repo.repo,
            branch=repo.branch,
            root_spec_path=repo.root_spec_path,
            github_token=repo.github_token,
        )
        for repo in repos
    ]
    return ExportRepositoriesResponse(repositories=items)


@router.get("", response_model=dict)
def get_repositories(
    request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all repositories."""
    client_tz = get_client_timezone(request)
    repos = db.query(Repository).all()
    items = []
    for repo in repos:
        items.append(
            {
                "id": repo.id,
                "owner": repo.owner,
                "repo": repo.repo,
                "branch": repo.branch,
                "root_spec_path": repo.root_spec_path,
                "has_github_token": repo.github_token is not None,
                "github_token_created_at": convert_to_client_timezone(
                    repo.github_token_created_at, client_tz
                ),
                "github_token_updated_at": convert_to_client_timezone(
                    repo.github_token_updated_at, client_tz
                ),
                "created_at": convert_to_client_timezone(repo.created_at, client_tz)
                or "",
                "updated_at": convert_to_client_timezone(repo.updated_at, client_tz),
            }
        )
    return {"items": items, "total": len(items)}


@router.post(
    "", response_model=CreateRepositoryResponse, status_code=status.HTTP_201_CREATED
)
def create_repository(
    request: CreateRepositoryRequest,
    http_request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new repository. Sync to github_client first; only persist to DB on success."""
    # Check if repository already exists
    existing = (
        db.query(Repository)
        .filter(
            Repository.owner == request.owner,
            Repository.repo == request.repo,
            Repository.branch == request.branch,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository already exists",
        )

    if mcp_server.github_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="github_client not available, cannot sync repository",
        )

    # Sync with github_client first; do not create DB entry if sync fails
    try:
        mcp_server.github_client.add_repository(
            owner=request.owner,
            repo=request.repo,
            branch=request.branch,
            root_spec_path=request.root_spec_path,
            github_token=request.github_token,
        )
        logger.info(
            f"Successfully synced repository {request.owner}/{request.repo}/{request.branch} to github_client"
        )
    except Exception as e:
        logger.error(
            f"Failed to sync repository {request.owner}/{request.repo}/{request.branch} to github_client: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync repository. Please check your repository settings and GitHub token.",
        ) from e

    # Sync succeeded; create DB entry
    repo = Repository(
        owner=request.owner,
        repo=request.repo,
        branch=request.branch,
        root_spec_path=request.root_spec_path,
    )
    github_token_plain = None
    if request.github_token:
        repo.github_token = request.github_token
        repo.github_token_created_at = get_utc_now()
        github_token_plain = request.github_token  # Return once

    db.add(repo)
    db.commit()
    db.refresh(repo)

    client_tz = get_client_timezone(http_request)
    response_data = {
        "id": repo.id,
        "owner": repo.owner,
        "repo": repo.repo,
        "branch": repo.branch,
        "root_spec_path": repo.root_spec_path,
        "has_github_token": repo.github_token is not None,
        "github_token_created_at": convert_to_client_timezone(
            repo.github_token_created_at, client_tz
        ),
        "github_token_updated_at": convert_to_client_timezone(
            repo.github_token_updated_at, client_tz
        ),
        "created_at": convert_to_client_timezone(repo.created_at, client_tz) or "",
        "updated_at": convert_to_client_timezone(repo.updated_at, client_tz),
    }

    if github_token_plain:
        response_data["github_token"] = github_token_plain

    return CreateRepositoryResponse(**response_data)


@router.patch("/{repo_id}", response_model=RepositoryResponse)
def update_repository(
    repo_id: int,
    request: UpdateRepositoryRequest,
    http_request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update repository configuration. Sync to github_client first; only update DB on success."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    old_owner = repo.owner
    old_repo = repo.repo
    old_branch = repo.branch

    if mcp_server.github_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="github_client not available, cannot sync repository",
        )

    # Sync with github_client first; do not update DB if sync fails
    new_owner = request.owner if request.owner is not None else repo.owner
    new_repo = request.repo if request.repo is not None else repo.repo
    new_branch = request.branch if request.branch is not None else repo.branch
    try:
        mcp_server.github_client.update_repository(
            owner=old_owner,
            repo=old_repo,
            branch=old_branch,
            new_owner=request.owner,
            new_repo=request.repo,
            new_branch=request.branch,
            new_root_spec_path=request.root_spec_path,
            new_github_token=request.github_token,
        )
        logger.info(
            f"Successfully synced repository update from {old_owner}/{old_repo}/{old_branch} to {new_owner}/{new_repo}/{new_branch} in github_client"
        )
    except Exception as e:
        logger.error(
            f"Failed to sync repository update {old_owner}/{old_repo}/{old_branch} to github_client: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to sync repository update. Please check your repository settings and GitHub token.",
        ) from e

    # Sync succeeded; update DB
    github_token_plain = None
    if request.owner is not None:
        repo.owner = request.owner
    if request.repo is not None:
        repo.repo = request.repo
    if request.branch is not None:
        repo.branch = request.branch
    if request.root_spec_path is not None:
        repo.root_spec_path = request.root_spec_path
    if request.github_token is not None:
        repo.github_token = request.github_token
        if repo.github_token_created_at is None:
            repo.github_token_created_at = get_utc_now()
        repo.github_token_updated_at = get_utc_now()
        github_token_plain = request.github_token  # Return once

    db.commit()
    db.refresh(repo)

    client_tz = get_client_timezone(http_request)
    response_data = {
        "id": repo.id,
        "owner": repo.owner,
        "repo": repo.repo,
        "branch": repo.branch,
        "root_spec_path": repo.root_spec_path,
        "has_github_token": repo.github_token is not None,
        "github_token_created_at": convert_to_client_timezone(
            repo.github_token_created_at, client_tz
        ),
        "github_token_updated_at": convert_to_client_timezone(
            repo.github_token_updated_at, client_tz
        ),
        "created_at": convert_to_client_timezone(repo.created_at, client_tz) or "",
        "updated_at": convert_to_client_timezone(repo.updated_at, client_tz),
    }

    if github_token_plain:
        response_data["github_token"] = github_token_plain

    return RepositoryResponse(**response_data)


@router.delete("/{repo_id}", status_code=status.HTTP_200_OK)
def delete_repository(
    repo_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    # Save repository info before deletion (needed for github_client sync)
    owner = repo.owner
    repo_name = repo.repo
    branch = repo.branch

    db.delete(repo)
    db.commit()

    if mcp_server.github_client is None:
        logger.warning(
            "github_client not available, repository deletion will be skipped"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    # Sync with github_client
    if mcp_server.github_client is not None:
        try:
            mcp_server.github_client.remove_repository(
                owner=owner, repo=repo_name, branch=branch
            )
            logger.info(
                f"Successfully synced repository deletion {owner}/{repo_name}/{branch} to github_client"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync repository deletion {owner}/{repo_name}/{branch} to github_client: {e}",
                exc_info=True,
            )
            # Don't fail the request if sync fails, just log the error

    return {"message": "Repository deleted successfully"}


@router.put("/{repo_id}/github-token", response_model=SetGithubTokenResponse)
def set_github_token(
    repo_id: int,
    request: SetGithubTokenRequest,
    http_request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Set GitHub token for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    repo.github_token = request.github_token
    if repo.github_token_created_at is None:
        repo.github_token_created_at = get_utc_now()
    repo.github_token_updated_at = get_utc_now()

    db.commit()
    db.refresh(repo)

    # Sync with github_client
    if mcp_server.github_client is not None:
        try:
            mcp_server.github_client.update_repository(
                owner=repo.owner,
                repo=repo.repo,
                branch=repo.branch,
                new_github_token=request.github_token,
            )
            logger.info(
                f"Successfully synced github_token for {repo.owner}/{repo.repo}/{repo.branch} to github_client"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync github_token for {repo.owner}/{repo.repo}/{repo.branch} to github_client: {e}",
                exc_info=True,
            )

    client_tz = get_client_timezone(http_request)
    return SetGithubTokenResponse(
        id=repo.id,
        github_token=request.github_token,  # Return once
        github_token_created_at=convert_to_client_timezone(
            repo.github_token_created_at, client_tz
        )
        or "",
        github_token_updated_at=convert_to_client_timezone(
            repo.github_token_updated_at, client_tz
        ),
    )


@router.patch("/{repo_id}/github-token", response_model=SetGithubTokenResponse)
def update_github_token(
    repo_id: int,
    request: SetGithubTokenRequest,
    http_request: Request,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update GitHub token for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    repo.github_token = request.github_token
    repo.github_token_updated_at = get_utc_now()

    db.commit()
    db.refresh(repo)

    # Sync with github_client
    if mcp_server.github_client is not None:
        try:
            mcp_server.github_client.update_repository(
                owner=repo.owner,
                repo=repo.repo,
                branch=repo.branch,
                new_github_token=request.github_token,
            )
            logger.info(
                f"Successfully synced github_token update for {repo.owner}/{repo.repo}/{repo.branch} to github_client"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync github_token update for {repo.owner}/{repo.repo}/{repo.branch} to github_client: {e}",
                exc_info=True,
            )

    client_tz = get_client_timezone(http_request)
    return SetGithubTokenResponse(
        id=repo.id,
        github_token=request.github_token,  # Return once
        github_token_created_at=convert_to_client_timezone(
            repo.github_token_created_at, client_tz
        )
        if repo.github_token_created_at
        else convert_to_client_timezone(get_utc_now(), client_tz) or "",
        github_token_updated_at=convert_to_client_timezone(
            repo.github_token_updated_at, client_tz
        )
        or "",
    )


@router.delete("/{repo_id}/github-token", status_code=status.HTTP_200_OK)
def delete_github_token(
    repo_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete GitHub token for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    # Save repo info before clearing token (for github_client sync)
    owner = repo.owner
    repo_name = repo.repo
    branch = repo.branch

    repo.github_token = None
    repo.github_token_created_at = None
    repo.github_token_updated_at = None

    db.commit()

    # Sync with github_client - set token to None
    if mcp_server.github_client is not None:
        try:
            # Find and update the repository in github_client
            for r in mcp_server.github_client.repos:
                if r["owner"] == owner and r["repo"] == repo_name and r["branch"] == branch:
                    r["github_token"] = None
                    logger.info(
                        f"Successfully cleared github_token for {owner}/{repo_name}/{branch} in github_client"
                    )
                    break
        except Exception as e:
            logger.error(
                f"Failed to clear github_token for {owner}/{repo_name}/{branch} in github_client: {e}",
                exc_info=True,
            )

    return {"message": "GitHub Token deleted successfully"}


@router.post("/{repo_id}/github-token/verify", response_model=VerifyGithubTokenResponse)
def verify_github_token(
    repo_id: int,
    admin=Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Verify GitHub token for a repository."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if not repo.github_token:
        return VerifyGithubTokenResponse(
            valid=False,
            error="No GitHub token configured",
        )

    try:
        token = repo.github_token
        # Verify token with GitHub API
        headers = {"Authorization": f"token {token}"}
        response = requests.get(
            "https://api.github.com/user", headers=headers, timeout=5
        )

        if response.status_code == 200:
            # Get rate limit
            rate_limit = response.headers.get("X-RateLimit-Remaining")
            # Get scopes from token (if available)
            scopes = (
                response.headers.get("X-OAuth-Scopes", "").split(", ")
                if response.headers.get("X-OAuth-Scopes")
                else None
            )

            return VerifyGithubTokenResponse(
                valid=True,
                scopes=scopes if scopes and scopes[0] else None,
                rate_limit_remaining=int(rate_limit) if rate_limit else None,
            )
        else:
            return VerifyGithubTokenResponse(
                valid=False,
                error=f"GitHub API returned status {response.status_code}",
            )
    except Exception as e:
        return VerifyGithubTokenResponse(
            valid=False,
            error=str(e),
        )
