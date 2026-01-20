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
from ..auth.encryption import encrypt_token, decrypt_token
from ..utils.datetime_utils import (
    get_utc_now,
    convert_to_client_timezone,
    get_client_timezone,
)

# Import github_client from mcp_server module
try:
    from ..mcp_server.mcp_server import github_client
except ImportError:
    github_client = None
    logger.warning("github_client not available, repository sync will be skipped")

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
                "has_github_token": repo.github_token_encrypted is not None,
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
    """Create a new repository."""
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

    repo = Repository(
        owner=request.owner,
        repo=request.repo,
        branch=request.branch,
        root_spec_path=request.root_spec_path,
    )

    github_token_plain = None
    if request.github_token:
        repo.github_token_encrypted = encrypt_token(request.github_token)
        repo.github_token_created_at = get_utc_now()
        github_token_plain = request.github_token  # Return once

    db.add(repo)
    db.commit()
    db.refresh(repo)

    # Sync with github_client
    if github_client is not None:
        try:
            github_client.add_repository(
                owner=repo.owner,
                repo=repo.repo,
                branch=repo.branch,
                root_spec_path=repo.root_spec_path,
            )
            logger.info(
                f"Successfully synced repository {repo.owner}/{repo.repo}/{repo.branch} to github_client"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync repository {repo.owner}/{repo.repo}/{repo.branch} to github_client: {e}",
                exc_info=True,
            )
            # Don't fail the request if sync fails, just log the error
    else:
        logger.warning("github_client not available, repository sync will be skipped")

    client_tz = get_client_timezone(http_request)
    response_data = {
        "id": repo.id,
        "owner": repo.owner,
        "repo": repo.repo,
        "branch": repo.branch,
        "root_spec_path": repo.root_spec_path,
        "has_github_token": repo.github_token_encrypted is not None,
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
    """Update repository configuration."""
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    # Save old values before updating (needed for github_client sync)
    old_owner = repo.owner
    old_repo = repo.repo
    old_branch = repo.branch

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
        repo.github_token_encrypted = encrypt_token(request.github_token)
        if repo.github_token_created_at is None:
            repo.github_token_created_at = get_utc_now()
        repo.github_token_updated_at = get_utc_now()
        github_token_plain = request.github_token  # Return once

    db.commit()
    db.refresh(repo)

    # Sync with github_client
    if github_client is not None:
        try:
            github_client.update_repository(
                owner=old_owner,
                repo=old_repo,
                branch=old_branch,
                new_owner=request.owner if request.owner is not None else None,
                new_repo=request.repo if request.repo is not None else None,
                new_branch=request.branch if request.branch is not None else None,
                new_root_spec_path=request.root_spec_path
                if request.root_spec_path is not None
                else None,
            )
            logger.info(
                f"Successfully synced repository update from {old_owner}/{old_repo}/{old_branch} to {repo.owner}/{repo.repo}/{repo.branch} in github_client"
            )
        except Exception as e:
            logger.error(
                f"Failed to sync repository update {repo.owner}/{repo.repo}/{repo.branch} to github_client: {e}",
                exc_info=True,
            )
            # Don't fail the request if sync fails, just log the error

    client_tz = get_client_timezone(http_request)
    response_data = {
        "id": repo.id,
        "owner": repo.owner,
        "repo": repo.repo,
        "branch": repo.branch,
        "root_spec_path": repo.root_spec_path,
        "has_github_token": repo.github_token_encrypted is not None,
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

    # Sync with github_client
    if github_client is not None:
        try:
            github_client.remove_repository(owner=owner, repo=repo_name, branch=branch)
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

    repo.github_token_encrypted = encrypt_token(request.github_token)
    if repo.github_token_created_at is None:
        repo.github_token_created_at = get_utc_now()
    repo.github_token_updated_at = get_utc_now()

    db.commit()
    db.refresh(repo)

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

    repo.github_token_encrypted = encrypt_token(request.github_token)
    repo.github_token_updated_at = get_utc_now()

    db.commit()
    db.refresh(repo)

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

    repo.github_token_encrypted = None
    repo.github_token_created_at = None
    repo.github_token_updated_at = None

    db.commit()
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

    if not repo.github_token_encrypted:
        return VerifyGithubTokenResponse(
            valid=False,
            error="No GitHub token configured",
        )

    try:
        token = decrypt_token(repo.github_token_encrypted)
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
