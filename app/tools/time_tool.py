from datetime import datetime
import pytz
from langchain.tools import tool

@tool
def get_current_time(timezone: str = "Asia/Karachi") -> dict:
    """
    Returns the current time for a given timezone.
    If no timezone is provided, defaults to Asia/Karachi.
    """
    try:
        tz = pytz.timezone(timezone)
    except Exception:
        tz = pytz.timezone("Asia/Karachi")

    now = datetime.now(tz)

    return {
        "time": now.strftime("%H:%M:%S"),
        "timezone": timezone
    }
