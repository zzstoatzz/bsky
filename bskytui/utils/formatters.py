from datetime import datetime

from zoneinfo import ZoneInfo

from bskytui.config.settings import Settings


def format_timestamp(timestamp: str) -> str:
    """Convert ISO timestamp to human readable format using configured timezone."""
    settings = Settings()
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    try:
        local_dt = dt.astimezone(ZoneInfo(settings.timezone))
    except Exception:
        local_dt = dt.astimezone(ZoneInfo("UTC"))
    return local_dt.strftime("%b %d, %I:%M %p")
