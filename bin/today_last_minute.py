#!/usr/bin/env python3

import datetime


def get_time_minutes(weekday, hour, minute):
    return (weekday * 24 * 60) + \
           (hour * 60) + \
           minute


end_of_today = datetime.datetime.combine(datetime.datetime.today(), datetime.time(23, 59, 59))
print(get_time_minutes(end_of_today.weekday(), end_of_today.hour, end_of_today.minute) + 1)
