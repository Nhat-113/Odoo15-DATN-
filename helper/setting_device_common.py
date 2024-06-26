from odoo import exceptions, _
from datetime import datetime
from itertools import chain


def is_overlapped_time(ranges):
    sorted_ranges = sorted(ranges, key=lambda begin_end: begin_end[0])
    return list(chain(*sorted_ranges)) != sorted(chain(*sorted_ranges))

def get_day_of_week_value(record):
    return [record['mon'], record['tue'], record['wed'], record['thu'], record['fri'], record['sat'], record['sun']]

def convert_string_to_time(time_string):
    return datetime.strptime(time_string, '%H:%M').time() 
    
def create_update_setting(device_id, settings, start_time, end_time, week_day):
    for rec in settings:
        start = convert_string_to_time(time_string=rec.start_time)
        end = convert_string_to_time(time_string=rec.end_time)
        overlapped_time = is_overlapped_time([(start, end), (start_time, end_time)])
        rec_week_day = get_day_of_week_value(rec)
                                
        day_overlapped = False
        for x,y in zip(week_day, rec_week_day):
            if x == y and x and y:
                day_overlapped = True
                break
        if overlapped_time and day_overlapped:
            raise exceptions.ValidationError(_("Device ID %(id)s was set from %(start)s to %(end)s", 
            id=device_id, start=start, end=end))