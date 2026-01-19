"""DateTime utilities for Context9."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import Request


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def format_datetime_iso(dt: Optional[datetime]) -> Optional[str]:
    """
    Format datetime to ISO 8601 format with UTC timezone indicator.

    If datetime is None, returns None.
    If datetime is naive (no timezone), assumes it's UTC.
    """
    if dt is None:
        return None

    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC if not already
    if dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    # Format as ISO 8601 with 'Z' suffix for UTC
    return dt.isoformat().replace("+00:00", "Z")


def get_client_timezone(request: Optional[Request] = None) -> str:
    """
    Get client timezone from request header.

    Checks for 'X-Timezone' header (e.g., 'Asia/Shanghai', 'America/New_York').
    Falls back to UTC if not provided.
    """
    if request is None:
        return "UTC"

    timezone_header = request.headers.get("X-Timezone")
    if timezone_header:
        return timezone_header

    return "UTC"


def convert_to_client_timezone(
    dt: Optional[datetime], client_tz: str = "UTC"
) -> Optional[str]:
    """
    Convert UTC datetime to client timezone and return as ISO string.

    Args:
        dt: UTC datetime (if naive, assumes UTC)
        client_tz: Client timezone string (e.g., 'Asia/Shanghai')

    Returns:
        ISO formatted datetime string in client timezone, or None if dt is None
    """
    if dt is None:
        return None

    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Convert to UTC if not already
    if dt.tzinfo != timezone.utc:
        dt = dt.astimezone(timezone.utc)

    # If client timezone is UTC, return as-is
    if client_tz == "UTC" or client_tz is None:
        return format_datetime_iso(dt)

    try:
        # Try to convert to client timezone (Python 3.9+)
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            # Fallback for Python < 3.9
            try:
                from backports.zoneinfo import ZoneInfo
            except ImportError:
                # If zoneinfo not available, fallback to UTC
                return format_datetime_iso(dt)

        client_tzinfo = ZoneInfo(client_tz)
        client_dt = dt.astimezone(client_tzinfo)
        return client_dt.isoformat()
    except (ValueError, KeyError):
        # Invalid timezone name, fallback to UTC
        return format_datetime_iso(dt)
