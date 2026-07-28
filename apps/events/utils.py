"""Utility functions for date/time handling and formatting in events."""

import datetime
import re

from django.utils.timezone import is_aware, make_aware


def seconds_resolution(dt):
    """Truncate a datetime to second precision by removing microseconds."""
    return dt - dt.microsecond * datetime.timedelta(0, 0, 1)


def minutes_resolution(dt):
    """Truncate a datetime to minute precision by removing seconds and microseconds."""
    return dt - dt.second * datetime.timedelta(0, 1, 0) - dt.microsecond * datetime.timedelta(0, 0, 1)


def date_to_datetime(date, tzinfo=None):
    """Convert a date to a timezone-aware datetime at midnight."""
    if tzinfo is None:
        tzinfo = datetime.UTC
    return datetime.datetime(*date.timetuple()[:6], tzinfo=tzinfo)


def extract_date_or_datetime(dt):
    """Convert a date to an aware datetime, passing through datetimes unchanged."""
    if isinstance(dt, datetime.date):
        return convert_dt_to_aware(dt)
    return dt


def convert_dt_to_aware(dt):
    """Ensure a datetime is timezone-aware, converting naive datetimes to UTC."""
    if not isinstance(dt, datetime.datetime):
        dt = date_to_datetime(dt)
    if not is_aware(dt):
        # we don't want to use get_current_timezone() because
        # settings.TIME_ZONE may be set something different than
        # UTC in the future
        return make_aware(dt, timezone=datetime.UTC)
    return dt


DAYS_PER_WEEK = 7
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60
DOUBLE_DIGIT_THRESHOLD = 9


def timedelta_nice_repr(timedelta, display="long", sep=", "):
    """Turn a datetime.timedelta object into a nice string repr.

    'display' can be 'minimal', 'short' or 'long' (default).

    Taken from bitbucket.org/schinckel/django-timedelta-field.
    'sql' and 'iso8601' support have been removed.
    """
    if not isinstance(timedelta, datetime.timedelta):
        msg = "First argument must be a timedelta."
        raise TypeError(msg)
    result = []
    weeks = int(timedelta.days / DAYS_PER_WEEK)
    days = timedelta.days % DAYS_PER_WEEK
    hours = int(timedelta.seconds / SECONDS_PER_HOUR)
    minutes = int((timedelta.seconds % SECONDS_PER_HOUR) / SECONDS_PER_MINUTE)
    seconds = timedelta.seconds % SECONDS_PER_MINUTE
    if display == "minimal":
        words = ["w", "d", "h", "m", "s"]
    elif display == "short":
        words = [" wks", " days", " hrs", " min", " sec"]
    elif display == "long":
        words = [" weeks", " days", " hours", " minutes", " seconds"]
    else:
        # Use django template-style formatting.
        # Valid values are d, g, G, h, H, i, s.
        return re.sub(r"([dgGhHis])", lambda x: f"%({x.group()})s", display) % {
            "d": days,
            "g": hours,
            "G": hours if hours > DOUBLE_DIGIT_THRESHOLD else f"0{hours}",
            "h": hours,
            "H": hours if hours > DOUBLE_DIGIT_THRESHOLD else f"0{hours}",
            "i": minutes if minutes > DOUBLE_DIGIT_THRESHOLD else f"0{minutes}",
            "s": seconds if seconds > DOUBLE_DIGIT_THRESHOLD else f"0{seconds}",
        }
    values = [weeks, days, hours, minutes, seconds]
    for i in range(len(values)):
        if values[i]:
            if values[i] == 1 and len(words[i]) > 1:
                result.append(f"{values[i]}{words[i].rstrip('s')}")
            else:
                result.append(f"{values[i]}{words[i]}")
    # Values with less than one second, which are considered zeroes.
    if len(result) == 0:
        # Display as 0 of the smallest unit.
        result.append(f"0{words[-1]}")
    return sep.join(result)


def timedelta_parse(string):
    """Parse a string into a timedelta object.

    Taken from bitbucket.org/schinckel/django-timedelta-field.
    """
    string = string.strip()
    if not string:
        msg = f"{string!r} is not a valid time interval"
        raise TypeError(msg)
    # This is the format we get from sometimes PostgreSQL, sqlite,
    # and from serialization.
    d = re.match(
        r"^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):"
        r"(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$",
        string,
    )
    if d:
        d = d.groupdict(0)
        if d["sign"] == "-":
            for k in "hours", "minutes", "seconds":
                d[k] = "-" + d[k]
        d.pop("sign", None)
    else:
        # This is the more flexible format.
        d = re.match(
            r"^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?"
            r"((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?"
            r"((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?"
            r"((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?"
            r"((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$",
            string,
        )
        if not d:
            msg = f"{string!r} is not a valid time interval"
            raise TypeError(msg)
        d = d.groupdict(0)
    return datetime.timedelta(**{k: float(v) for k, v in d.items()})
