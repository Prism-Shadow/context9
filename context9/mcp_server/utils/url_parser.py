"""
URL Parser for remotedoc:// URLs.

This module handles parsing and validation of remotedoc:// URLs.
"""

import re
from urllib.parse import unquote


class URLParseError(Exception):
    """Raised when URL parsing fails."""

    pass


def parse_remotedoc_url(url: str) -> str:
    """
    Parse a remotedoc:// URL and extract the file path.

    Args:
        url: A remotedoc:// URL, e.g., "remotedoc://spec.md" or "remotedoc://docs/gemini/spec.md"

    Returns:
        The file path extracted from the URL, e.g., "spec.md" or "docs/gemini/spec.md"

    Raises:
        URLParseError: If the URL format is invalid
    """
    if not url:
        raise URLParseError("URL cannot be empty")

    # Remove whitespace
    url = url.strip()

    # Check if URL starts with remotedoc://
    if not url.startswith("remotedoc://"):
        raise URLParseError(
            f"Invalid URL format: must start with 'remotedoc://'. Got: {url}"
        )

    # Extract the path part after remotedoc://
    path = url[12:]  # len("remotedoc://") = 12

    if not path:
        raise URLParseError("URL must include a file path after 'remotedoc://'")

    # URL decode the path
    try:
        path = unquote(path)
    except Exception as e:
        raise URLParseError(f"Failed to decode URL: {e}")

    # Normalize the path
    path = normalize_path(path)

    # Validate path
    if not is_valid_path(path):
        raise URLParseError(f"Invalid file path: {path}")

    return path


def normalize_path(path: str) -> str:
    """
    Normalize a file path by removing redundant slashes and resolving relative components.

    Args:
        path: The file path to normalize

    Returns:
        Normalized file path
    """
    # Remove leading and trailing slashes
    path = path.strip("/")

    # Remove redundant slashes
    path = re.sub(r"/+", "/", path)

    # Remove . and .. components (basic normalization)
    parts = []
    for part in path.split("/"):
        if part == ".":
            continue
        elif part == "..":
            if parts:
                parts.pop()
        elif part:
            parts.append(part)

    return "/".join(parts)


def is_valid_path(path: str) -> bool:
    """
    Validate that a path is safe and valid.

    Args:
        path: The file path to validate

    Returns:
        True if the path is valid, False otherwise
    """
    if not path:
        return False

    # Check for path traversal attempts
    if ".." in path:
        return False

    # Check for absolute paths (should be relative)
    if path.startswith("/"):
        return False

    # Check for invalid characters (basic check)
    invalid_chars = ["\x00", "\r", "\n"]
    for char in invalid_chars:
        if char in path:
            return False

    return True
