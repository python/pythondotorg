import datetime
import re

import pytz

from django.utils.timezone import make_aware, is_aware


def seconds_resolution(dt):
    return dt - dt.microsecond * datetime.timedelta(0, 0, 1)


def minutes_resolution(dt):
    return dt - dt.second * datetime.timedelta(0, 1, 0) - dt.microsecond * datetime.timedelta(0, 0, 1)


def date_to_datetime(date, tzinfo=None):
    if tzinfo is None:
        tzinfo = pytz.UTC
    return datetime.datetime(*date.timetuple()[:6], tzinfo=tzinfo)


def extract_date_or_datetime(dt):
    if isinstance(dt, datetime.datetime):
        return convert_dt_to_aware(dt)
    return dt


def convert_dt_to_aware(dt):
    if not isinstance(dt, datetime.datetime):
        dt = date_to_datetime(dt)
    if not is_aware(dt):
        # we don't want to use get_current_timezone() because
        # settings.TIME_ZONE may be set something different than
        # UTC in the future
        return make_aware(dt, timezone=pytz.UTC)
    return dt


def timedelta_nice_repr(timedelta, display='long', sep=', '):
    """
    Turns a datetime.timedelta object into a nice string repr.

    'display' can be 'minimal', 'short' or 'long' (default).

    Taken from bitbucket.org/schinckel/django-timedelta-field.
    'sql' and 'iso8601' support have been removed.
    """
    if not isinstance(timedelta, datetime.timedelta):
        raise TypeError('First argument must be a timedelta.')
    result = []
    weeks = int(timedelta.days / 7)
    days = timedelta.days % 7
    hours = int(timedelta.seconds / 3600)
    minutes = int((timedelta.seconds % 3600) / 60)
    seconds = timedelta.seconds % 60
    if display == 'minimal':
        words = ['w', 'd', 'h', 'm', 's']
    elif display == 'short':
        words = [' wks', ' days', ' hrs', ' min', ' sec']
    elif display == 'long':
        words = [' weeks', ' days', ' hours', ' minutes', ' seconds']
    else:
        # Use django template-style formatting.
        # Valid values are d, g, G, h, H, i, s.
        return re.sub(r'([dgGhHis])', lambda x: '%%(%s)s' % x.group(), display) % {
            'd': days,
            'g': hours,
            'G': hours if hours > 9 else '0%s' % hours,
            'h': hours,
            'H': hours if hours > 9 else '0%s' % hours,
            'i': minutes if minutes > 9 else '0%s' % minutes,
            's': seconds if seconds > 9 else '0%s' % seconds
        }
    values = [weeks, days, hours, minutes, seconds]
    for i in range(len(values)):
        if values[i]:
            if values[i] == 1 and len(words[i]) > 1:
                result.append('%i%s' % (values[i], words[i].rstrip('s')))
            else:
                result.append('%i%s' % (values[i], words[i]))
    # Values with less than one second, which are considered zeroes.
    if len(result) == 0:
        # Display as 0 of the smallest unit.
        result.append('0%s' % (words[-1]))
    return sep.join(result)


def timedelta_parse(string):
    """
    Parse a string into a timedelta object.

    Taken from bitbucket.org/schinckel/django-timedelta-field.
    """
    string = string.strip()
    if not string:
        raise TypeError('{!r} is not a valid time interval'.format(string))
    # This is the format we get from sometimes PostgreSQL, sqlite,
    # and from serialization.
    d = re.match(
        r'^((?P<days>[-+]?\d+) days?,? )?(?P<sign>[-+]?)(?P<hours>\d+):'
        r'(?P<minutes>\d+)(:(?P<seconds>\d+(\.\d+)?))?$',
        string
    )
    if d:
        d = d.groupdict(0)
        if d['sign'] == '-':
            for k in 'hours', 'minutes', 'seconds':
                d[k] = '-' + d[k]
        d.pop('sign', None)
    else:
        # This is the more flexible format.
        d = re.match(
            r'^((?P<weeks>-?((\d*\.\d+)|\d+))\W*w((ee)?(k(s)?)?)(,)?\W*)?'
            r'((?P<days>-?((\d*\.\d+)|\d+))\W*d(ay(s)?)?(,)?\W*)?'
            r'((?P<hours>-?((\d*\.\d+)|\d+))\W*h(ou)?(r(s)?)?(,)?\W*)?'
            r'((?P<minutes>-?((\d*\.\d+)|\d+))\W*m(in(ute)?(s)?)?(,)?\W*)?'
            r'((?P<seconds>-?((\d*\.\d+)|\d+))\W*s(ec(ond)?(s)?)?)?\W*$',
            string
        )
        if not d:
            raise TypeError('{!r} is not a valid time interval'.format(string))
        d = d.groupdict(0)
    return datetime.timedelta(**{k: float(v) for k, v in d.items()})
