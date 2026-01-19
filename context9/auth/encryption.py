"""GitHub Token encryption using Fernet."""

import os
import base64
from cryptography.fernet import Fernet
from loguru import logger

# Get encryption key from environment
ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Generate a new key for development (WARNING: Not secure for production!)
    logger.warning(
        "GITHUB_TOKEN_ENCRYPTION_KEY not set, generating a new key (not secure for production!)"
    )
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning(f"Generated encryption key: {ENCRYPTION_KEY}")
    logger.warning(
        "Please set GITHUB_TOKEN_ENCRYPTION_KEY environment variable in production!"
    )


def get_fernet() -> Fernet:
    """Get Fernet instance for encryption/decryption."""
    try:
        key = (
            ENCRYPTION_KEY.encode()
            if isinstance(ENCRYPTION_KEY, str)
            else ENCRYPTION_KEY
        )
        return Fernet(key)
    except Exception as e:
        logger.error(f"Failed to initialize Fernet: {e}")
        raise


def encrypt_token(token: str) -> str:
    """Encrypt GitHub Token."""
    f = get_fernet()
    encrypted = f.encrypt(token.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt GitHub Token."""
    f = get_fernet()
    encrypted = base64.b64decode(encrypted_token.encode())
    return f.decrypt(encrypted).decode()
