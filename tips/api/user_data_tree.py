import datetime
import objectpath
import pytz
from dateutil import parser
from objectpath.utils import timeutils


# taken concept from https://stackoverflow.com/a/9388462/756075
def yearsAgo(datestring):
    subject_date = parser.isoparse(datestring)
    today = datetime.date.today()
    years = today.year - subject_date.year
    if (
        today.month < subject_date.month
        or today.month == subject_date.month
        and today.day < subject_date.day
    ):
        years -= 1

    return years


def strToUtcDateTime(datestring):
    if not datestring:
        return None

    date_parts = datestring.split("T")
    date_segments = [int(x) for x in date_parts[0].split("-")[:3]]
    dt = timeutils.dateTime([date_segments, [0, 0, 0]])
    dt = pytz.UTC.localize(dt)
    return dt


class UserDataTree(objectpath.Tree):
    def __init__(self, obj, cfg=None):
        super().__init__(obj, cfg)
        self.register_function("yearsAgo", yearsAgo)
        self.register_function("today", lambda: datetime.date.today())
        self.register_function(
            "strToUtcDateTime",
            strToUtcDateTime,
        )
