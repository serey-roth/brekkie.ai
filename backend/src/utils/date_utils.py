from datetime import datetime, timezone


def to_utc_isostring(dt: datetime) -> str:
    """Convert naive UTC datetime to ISO string with timezone info."""
    return dt.replace(tzinfo=timezone.utc).isoformat()


def strip_timezone(dt: datetime) -> datetime:
    """Strip timezone info from datetime."""
    return dt.replace(tzinfo=None)
