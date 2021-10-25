import datetime
import objectpath

from dateutil import parser


# taken concept from https://stackoverflow.com/a/9388462/756075
def yearsAgo(datestring):
    subject_date = parser.isoparse(datestring)
    today = datetime.date.today()
    years = today.year - subject_date.year
    if today.month < subject_date.month or today.month == subject_date.month and today.day < subject_date.day:
        years -= 1

    return years


class UserDataTree(objectpath.Tree):
    def __init__(self, obj, cfg=None):
        super().__init__(obj, cfg)
        self.register_function('yearsAgo', yearsAgo)
