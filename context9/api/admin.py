"""Admin authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta
from loguru import logger

from ..database import get_db
from ..database.models import Admin
from ..auth.admin_auth import (
    authenticate_admin,
    create_access_token,
    get_current_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from ..auth.password import verify_password, get_password_hash

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: dict


class AdminResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login."""
    logger.info(f"Login attempt for username: {request.username}")
    admin = authenticate_admin(request.username, request.password, db)
    if not admin:
        logger.warning(f"Login failed for username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    logger.info(f"Login successful for username: {request.username}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin.username}, expires_delta=access_token_expires
    )
    return LoginResponse(
        access_token=access_token,
        admin={"id": admin.id, "username": admin.username},
    )


@router.get("/me", response_model=AdminResponse)
def get_me(admin: Admin = Depends(get_current_admin)):
    """Get current admin information."""
    return AdminResponse(id=admin.id, username=admin.username)


@router.post("/logout")
def logout(admin: Admin = Depends(get_current_admin)):
    """Logout (client should discard token)."""
    return {"message": "Logged out successfully"}


@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Change admin password."""
    logger.info(f"Password change request for admin: {admin.username}")

    # Verify current password
    if not verify_password(request.current_password, admin.password_hash):
        logger.warning(
            f"Current password verification failed for admin: {admin.username}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if not request.new_password or len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters long",
        )

    # Update password
    admin.password_hash = get_password_hash(request.new_password)
    db.commit()
    db.refresh(admin)

    logger.info(f"Password changed successfully for admin: {admin.username}")
    return {"message": "Password changed successfully"}
