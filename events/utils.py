import datetime
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


def convert_dt_to_aware(dt):
    if not isinstance(dt, datetime.datetime):
        dt = date_to_datetime(dt)
    if not is_aware(dt):
        # we don't want to use get_current_timezone() because
        # settings.TIME_ZONE may be set something different than
        # UTC in the future
        return make_aware(dt, timezone=pytz.UTC)
    return dt
