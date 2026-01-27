"""API Key management routes."""

import secrets
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import get_db
from ..database.models import Admin, ApiKey, Repository, ApiKeyRepository
from ..auth.admin_auth import get_current_admin
from ..utils.datetime_utils import convert_to_client_timezone, get_client_timezone

router = APIRouter()


class CreateApiKeyRequest(BaseModel):
    name: str


class CreateApiKeyResponse(BaseModel):
    id: int
    name: str
    key_value: str
    created_at: str

    class Config:
        from_attributes = True


class UpdateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str | None = None
    repository_count: int = 0

    class Config:
        from_attributes = True


class ApiKeyDetailResponse(BaseModel):
    id: int
    name: str
    created_at: str
    updated_at: str | None = None
    repositories: List[dict]

    class Config:
        from_attributes = True


class UpdateApiKeyRepositoriesRequest(BaseModel):
    repository_ids: List[int]


def generate_api_key() -> tuple[str, str]:
    """Generate a new API key."""
    # Generate 32 random bytes
    random_bytes = secrets.token_bytes(32)
    # Convert to hex string
    key_value = "ctx9_" + random_bytes.hex()
    # Hash the key
    key_hash = hashlib.sha256(key_value.encode()).hexdigest()
    return key_value, key_hash


@router.get("", response_model=dict)
def get_api_keys(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get all API keys."""
    client_tz = get_client_timezone(request)
    api_keys = db.query(ApiKey).all()
    items = []
    for key in api_keys:
        repo_count = (
            db.query(ApiKeyRepository)
            .filter(ApiKeyRepository.api_key_id == key.id)
            .count()
        )
        items.append(
            {
                "id": key.id,
                "name": key.name,
                "created_at": convert_to_client_timezone(key.created_at, client_tz),
                "updated_at": convert_to_client_timezone(key.updated_at, client_tz),
                "repository_count": repo_count,
            }
        )
    return {"items": items, "total": len(items)}


@router.post(
    "", response_model=CreateApiKeyResponse, status_code=status.HTTP_201_CREATED
)
def create_api_key(
    request: CreateApiKeyRequest,
    http_request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new API key with access to all repositories by default."""
    client_tz = get_client_timezone(http_request)
    key_value, key_hash = generate_api_key()
    api_key = ApiKey(
        name=request.name,
        key_hash=key_hash,
        key_value=key_value,
        created_by=admin.id,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    # Grant access to all existing repositories by default
    all_repos = db.query(Repository).all()
    for repo in all_repos:
        relation = ApiKeyRepository(api_key_id=api_key.id, repository_id=repo.id)
        db.add(relation)
    db.commit()

    return CreateApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        key_value=key_value,  # Return only once
        created_at=convert_to_client_timezone(api_key.created_at, client_tz) or "",
    )


@router.delete("/{key_id}", status_code=status.HTTP_200_OK)
def delete_api_key(
    key_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete an API key."""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    db.delete(api_key)
    db.commit()
    return {"message": "API Key deleted successfully"}


@router.patch("/{key_id}", response_model=ApiKeyResponse)
def update_api_key(
    key_id: int,
    request: UpdateApiKeyRequest,
    http_request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update API key name."""
    client_tz = get_client_timezone(http_request)
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    api_key.name = request.name
    db.commit()
    db.refresh(api_key)
    repo_count = (
        db.query(ApiKeyRepository).filter(ApiKeyRepository.api_key_id == key_id).count()
    )
    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        created_at=convert_to_client_timezone(api_key.created_at, client_tz) or "",
        updated_at=convert_to_client_timezone(api_key.updated_at, client_tz),
        repository_count=repo_count,
    )


@router.get("/{key_id}", response_model=ApiKeyDetailResponse)
def get_api_key_detail(
    key_id: int,
    http_request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Get API key detail with repositories."""
    client_tz = get_client_timezone(http_request)
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    repo_relations = (
        db.query(ApiKeyRepository).filter(ApiKeyRepository.api_key_id == key_id).all()
    )
    repositories = []
    for rel in repo_relations:
        repo = db.query(Repository).filter(Repository.id == rel.repository_id).first()
        if repo:
            repositories.append(
                {
                    "id": repo.id,
                    "owner": repo.owner,
                    "repo": repo.repo,
                    "branch": repo.branch,
                    "root_spec_path": repo.root_spec_path,
                }
            )
    return ApiKeyDetailResponse(
        id=api_key.id,
        name=api_key.name,
        created_at=convert_to_client_timezone(api_key.created_at, client_tz) or "",
        updated_at=convert_to_client_timezone(api_key.updated_at, client_tz),
        repositories=repositories,
    )


@router.put("/{key_id}/repositories", status_code=status.HTTP_200_OK)
def update_api_key_repositories(
    key_id: int,
    request: UpdateApiKeyRepositoriesRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Update API key repository permissions."""
    api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    # Delete existing relations
    db.query(ApiKeyRepository).filter(ApiKeyRepository.api_key_id == key_id).delete()
    # Create new relations
    for repo_id in request.repository_ids:
        # Verify repository exists
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            continue
        relation = ApiKeyRepository(api_key_id=key_id, repository_id=repo_id)
        db.add(relation)
    db.commit()
    return {"message": "Permissions updated successfully"}
