import datetime
import pytz


def seconds_resolution(dt):
    return dt - dt.microsecond * datetime.timedelta(0, 0, 1)


def minutes_resolution(dt):
    return dt - dt.second * datetime.timedelta(0, 1, 0) - dt.microsecond * datetime.timedelta(0, 0, 1)

def date_to_datetime(date, tzinfo=None):
    if tzinfo is None:
        tzinfo = pytz.UTC
    return datetime.datetime(*date.timetuple()[:6], tzinfo=tzinfo)
