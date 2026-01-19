"""Admin authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import timedelta

from ..database import get_db
from ..database.models import Admin
from ..auth.admin_auth import (
    authenticate_admin,
    create_access_token,
    get_current_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

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


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Admin login."""
    admin = authenticate_admin(request.username, request.password, db)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
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
