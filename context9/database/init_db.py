"""Database initialization script."""

import os
from loguru import logger
from .database import init_db, SessionLocal
from .models import Admin
from ..auth.password import get_password_hash


def create_default_admin(username: str = "admin", password: str = "admin123"):
    """Create default admin user if it doesn't exist."""
    db = SessionLocal()
    try:
        existing_admin = db.query(Admin).filter(Admin.username == username).first()
        if existing_admin:
            logger.info(f"Admin user '{username}' already exists")
            return existing_admin

        password_hash = get_password_hash(password)
        admin = Admin(username=username, password_hash=password_hash)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"Default admin user '{username}' created")
        return admin
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create default admin: {e}")
        raise
    finally:
        db.close()


def initialize_database():
    """Initialize database and create default admin."""
    init_db()

    # Create default admin from environment or use defaults
    admin_username = os.getenv("CONTEXT9_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("CONTEXT9_ADMIN_PASSWORD", "admin123")

    create_default_admin(admin_username, admin_password)
    logger.info("Database initialization completed")


if __name__ == "__main__":
    initialize_database()
