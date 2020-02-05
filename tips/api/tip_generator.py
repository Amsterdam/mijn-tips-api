import datetime
import json
import os
from typing import Union

import dateutil.parser
import pytz

from tips.config import PROJECT_PATH

TIPS_POOL_FILE = os.path.join(PROJECT_PATH, 'api', 'tips_pool.json')

FRONT_END_TIP_KEYS = ['datePublished', 'description', 'id', 'link', 'title', 'priority', 'imgUrl', 'isPersonalized']


tips_pool = []


def value_of(data: dict, path: str, default=None):
    """
    Try to get the value of path '.' with as separator. When not possible, return the default.
    :param data: data in which to search
    :param path: . separated path to the nested data
    :param default: value which is returned when path is not found
    :return: The value of path when found, otherwise default.

    TODO: how to deal with lists?
    """
    path_sep = path.split('.')
    value = data
    for part in path_sep:
        try:
            value = value[part]
        except KeyError:
            return default
    return value


def object_where(data: list, query: dict):
    """
    Select the first object that matches the query
    :param data: data in which to search
    :param query:
    :return: the first object that matches  # TODO: is the first a good idea?
    """
    for i in data:
        if type(i) == dict:
            try:
                for field_name, field_value in query.items():
                    if i[field_name] != field_value:
                        return None

                return i
            except KeyError:
                return None

        else:
            return None


def to_datetime(value: str):
    """ Converts a string containing an iso8601 date to a datetime object. """
    # 1950-01-01T00:00:00Z
    date = dateutil.parser.isoparse(value)

    return date


def is_18(value: Union[datetime.date, datetime.datetime, str]):
    return before_or_on(value, years=18)


def after(value: Union[datetime.date, datetime.datetime, str], **kwargs):
    return not before_or_on(value, **kwargs)


# TODO: better name
def before_or_on(value: Union[datetime.date, datetime.datetime, str], **kwargs):
    """
    Check if the value is before or on the specified timedelta values.
    # TODO: Improve docstring
    The keyword arguments are fed into a dateutils relative timedelta
    https://dateutil.readthedocs.io/en/stable/relativedelta.html

    """
    delta = dateutil.relativedelta.relativedelta(**kwargs)

    if type(value) == str:
        value = to_datetime(value)

    if type(value) == datetime.datetime:
        now = datetime.datetime.now(datetime.timezone.utc)

        # Set utz for dates which have no timezone
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)

        result = value <= now - delta
        return result
    elif type(value) == datetime.date:
        # Date has no timezone
        today = datetime.date.today()
        result = value <= today - delta
        return result


EVAL_GLOBALS = {
    "datetime": datetime.datetime,
    "timedelta": dateutil.relativedelta.relativedelta,
    "before_or_on": before_or_on,
    "after": after,
    "value_of": value_of,
    "object_where": object_where,
    "to_datetime": to_datetime,
    "is_18": is_18,
    "len": len,
}


def refresh_tips_pool():
    global tips_pool
    with open(TIPS_POOL_FILE) as fh:
        tips_pool = json.load(fh)


refresh_tips_pool()


def tip_filterer(tip, userdata):
    # if a tip has a conditional field, it must be true. If it does not. it's always included
    if not tip['active']:
        return False
    conditional = tip.get("conditional", None)
    if conditional is None or conditional == '':
        return tip
    try:
        eval_locals = {}
        if userdata['optin']:
            eval_locals['data'] = userdata['data']

        if eval(conditional, EVAL_GLOBALS, eval_locals):
            return tip
        else:
            return False
    except TypeError:  # Input must be a string. If its anything else, the tip conditional is malformed
        raise
    except Exception as e:
        print("!! Conditional exception: ", e)
        return False


def clean_tip(tip):
    """ Only select the relevant frontend fields and default isPersonalized to False. """
    if not tip.get('isPersonalized', False):
        tip['isPersonalized'] = False
    # Only add fields which are allowed to go to the frontend
    return {k: v for (k, v) in tip.items() if k in FRONT_END_TIP_KEYS}


def fix_id(tip, source):
    """ Some of our data sources do not follow our id guidelines, fix the tip here inplace. """
    if source == "belasting":
        tip['id'] = "belasting-" + str(tip['id'])


def format_tip(tip):
    if "link" in tip:
        link_data = tip["link"]
        link = {
            "title": link_data.get("title", None),
            "to": link_data.get("to", None)
        }
    else:
        link = {"title": None, "to": None}

    return {
        "id": tip.get('id', None),
        "active": True,
        "priority": tip.get('priority', None),
        "datePublished": tip.get('datePublished', None),
        "title": tip.get('title', None),
        "description": tip.get('description', None),
        "link": link,
        "imgUrl": tip.get("imgUrl")
    }


def get_tips_from_user_data(user_data):
    source_tips = []
    for source, value in user_data['data'].items():
        if type(value) == dict and 'tips' in value:
            for tip in value['tips']:
                fix_id(tip, source)
            source_tips = source_tips + value['tips']

    # make sure they follow the format
    source_tips = [format_tip(tip) for tip in source_tips]

    # remove any conditionals because of security
    for tip in source_tips:
        if 'conditional' in tip:
            del tip['conditional']

    return source_tips


def tips_generator(user_data, tips=None):
    """ Generate tips. """
    print("\n\n-----")
    if tips is None:
        tips = tips_pool

    # add source tips
    source_tips = get_tips_from_user_data(user_data)
    if source_tips:
        tips = tips + source_tips

    tips = [tip for tip in tips if tip_filterer(tip, user_data)]
    tips = [clean_tip(tip) for tip in tips]

    tips.sort(key=lambda t: t['priority'], reverse=True)

    return {
        "items": tips,
        "total": len(tips),
    }
