import datetime


def seconds_resolution(dt):
    return dt - dt.microsecond * datetime.timedelta(0, 0, 1)


def minutes_resolution(dt):
    return dt - dt.second * datetime.timedelta(0, 1, 0) - dt.microsecond * datetime.timedelta(0, 0, 1)
