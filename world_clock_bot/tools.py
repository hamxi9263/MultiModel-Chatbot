from datetime import datetime
import pytz

def get_current_time(timezone: str = "Asia/Karachi"):
    """
    Returns current time, date, and timezone.
    Defaults to Asia/Karachi if invalid.
    """
    try:
        tz = pytz.timezone(timezone)
    except Exception:
        tz = pytz.timezone("Asia/Karachi")
        timezone = "Asia/Karachi"

    now = datetime.now(tz)

    return {
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "timezone": timezone
    }
