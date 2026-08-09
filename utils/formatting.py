"""
The backend's CREATED_AT/UPDATED_AT come back as raw Unix epoch seconds
(confirmed from a live screenshot: 1786264857.52000 -- August 2026 in
epoch seconds), not ISO date strings. format_when() turns that into
something a person would actually want to read.
"""
from datetime import datetime, timezone


def _time_no_leading_zero(dt: datetime) -> str:
    t = dt.strftime("%I:%M %p")
    return t[1:] if t.startswith("0") else t


def format_when(value) -> str:
    if value in (None, ""):
        return "—"
    try:
        dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return str(value)[:16].replace("T", " ")

    now = datetime.now(tz=timezone.utc)
    seconds = (now - dt).total_seconds()

    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        m = int(seconds // 60)
        return f"{m} min{'s' if m != 1 else ''} ago"
    if dt.date() == now.date():
        h = int(seconds // 3600)
        return f"{h} hour{'s' if h != 1 else ''} ago"
    if (now.date() - dt.date()).days == 1:
        return f"Yesterday at {_time_no_leading_zero(dt)}"
    if (now.date() - dt.date()).days < 7:
        return f"{dt.strftime('%A')} at {_time_no_leading_zero(dt)}"
    return dt.strftime("%b %d, %Y")