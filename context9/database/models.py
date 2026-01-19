"""SQLAlchemy models for Context9."""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Admin(Base):
    """Admin user model."""

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship("ApiKey", back_populates="creator")


class ApiKey(Base):
    """API Key model."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    key_value = Column(
        String, unique=True, nullable=False
    )  # Only for initial generation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("admins.id"), nullable=True)

    # Relationships
    creator = relationship("Admin", back_populates="api_keys")
    repositories = relationship(
        "ApiKeyRepository", back_populates="api_key", cascade="all, delete-orphan"
    )


class Repository(Base):
    """Repository configuration model."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String, nullable=False)
    repo = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    root_spec_path = Column(String, default="spec.md")
    github_token_encrypted = Column(Text, nullable=True)
    github_token_created_at = Column(DateTime, nullable=True)
    github_token_updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    api_keys = relationship(
        "ApiKeyRepository", back_populates="repository", cascade="all, delete-orphan"
    )

    __table_args__ = ({"sqlite_autoincrement": True},)


class ApiKeyRepository(Base):
    """API Key to Repository association model."""

    __tablename__ = "api_key_repositories"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(
        Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False
    )
    repository_id = Column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    api_key = relationship("ApiKey", back_populates="repositories")
    repository = relationship("Repository", back_populates="api_keys")

    __table_args__ = ({"sqlite_autoincrement": True},)
