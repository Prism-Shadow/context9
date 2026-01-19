"""Password hashing and verification."""

import bcrypt
from loguru import logger

# Bcrypt has a maximum password length of 72 bytes
BCRYPT_MAX_PASSWORD_LENGTH = 72


def _truncate_password_bytes(password: str) -> bytes:
    """
    Truncate password to bcrypt's maximum length (72 bytes) and return as bytes.

    Bcrypt has a hard limit of 72 bytes for passwords. This function
    ensures the password is within that limit by truncating if necessary.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_LENGTH:
        logger.warning(
            f"Password length ({len(password_bytes)} bytes) exceeds bcrypt limit "
            f"({BCRYPT_MAX_PASSWORD_LENGTH} bytes). Truncating password."
        )
        return password_bytes[:BCRYPT_MAX_PASSWORD_LENGTH]
    return password_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    try:
        # Truncate password to match what was stored
        password_bytes = _truncate_password_bytes(plain_password)
        # hashed_password should be a string, convert to bytes if needed
        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode("utf-8")
        else:
            hashed_password_bytes = hashed_password
        return bcrypt.checkpw(password_bytes, hashed_password_bytes)
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a password."""
    # Truncate password to bcrypt's maximum length
    password_bytes = _truncate_password_bytes(password)
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string (decode from bytes)
    return hashed.decode("utf-8")
