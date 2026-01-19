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
        # Check if any admin exists
        admin_count = db.query(Admin).count()
        logger.info(f"Current admin count in database: {admin_count}")
        
        existing_admin = db.query(Admin).filter(Admin.username == username).first()
        if existing_admin:
            logger.info(f"Admin user '{username}' already exists")
            return existing_admin

        password_hash = get_password_hash(password)
        admin = Admin(username=username, password_hash=password_hash)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        logger.info(f"Default admin user '{username}' created successfully")
        return admin
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create default admin: {e}")
        raise
    finally:
        db.close()


def ensure_default_admin_exists():
    """Ensure that at least one admin user exists in the database."""
    db = SessionLocal()
    try:
        admin_count = db.query(Admin).count()
        if admin_count == 0:
            logger.warning("No admin users found in database. Creating default admin...")
            admin_username = os.getenv("CONTEXT9_ADMIN_USERNAME", "admin")
            admin_password = os.getenv("CONTEXT9_ADMIN_PASSWORD", "admin123")
            create_default_admin(admin_username, admin_password)
            logger.info("Default admin user created successfully")
        else:
            logger.info(f"Found {admin_count} admin user(s) in database")
    except Exception as e:
        logger.error(f"Failed to ensure default admin exists: {e}")
        raise
    finally:
        db.close()


def initialize_database():
    """Initialize database and create default admin."""
    try:
        init_db()
        logger.info("Database tables initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        raise

    # Create default admin from environment or use defaults
    admin_username = os.getenv("CONTEXT9_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("CONTEXT9_ADMIN_PASSWORD", "admin123")

    # Always try to create default admin - this function handles the case where admin already exists
    try:
        admin = create_default_admin(admin_username, admin_password)
        if admin:
            logger.info(f"Database initialization completed successfully. Default admin '{admin_username}' is available.")
        else:
            logger.warning("Database initialization completed but default admin creation returned None")
            # Try to ensure at least one admin exists
            ensure_default_admin_exists()
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        logger.error("This is a critical error. Admin login will not work until an admin user is created.")
        # Try one more time with ensure function
        try:
            logger.info("Attempting to ensure default admin exists...")
            ensure_default_admin_exists()
        except Exception as e2:
            logger.error(f"Second attempt to create admin also failed: {e2}")
            raise


if __name__ == "__main__":
    initialize_database()
