import zoneinfo
from datetime import datetime


def get_now():
    return datetime.now(zoneinfo.ZoneInfo("Africa/Algiers"))
