#!/usr/bin/env python3

import datetime


def get_time_minutes(weekday, hour, minute):
    return (weekday * 24 * 60) + \
           (hour * 60) + \
           minute


now = datetime.datetime.now()
print(get_time_minutes(now.weekday(), now.hour, now.minute))
