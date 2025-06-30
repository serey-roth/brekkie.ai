from datetime import datetime, timezone


def to_utc_isostring(dt: datetime | None) -> str | None:
    """Convert naive UTC datetime to ISO string with timezone info."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc).isoformat()


def strip_timezone(dt: datetime | None) -> datetime | None:
    """Strip timezone info from datetime."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None)