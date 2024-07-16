from odoo import fields, models
from odoo.osv.expression import OR

def generate_time_selection():
    time_selection = []
    start_hour = 0
    end_hour = 23
    end_minute = 30
    interval_minutes = 15

    for hour in range(start_hour, end_hour + 1):
        for minute in range(0, 60, interval_minutes):
            if hour == end_hour and minute > end_minute:
                break
            formatted_hour = str(hour).zfill(2)
            formatted_minute = str(minute).zfill(2)
            if hour >= 12:
                time_label = f"{formatted_hour}:{formatted_minute}"
            else:
                time_label = f"{formatted_hour}:{formatted_minute}"
            time_selection.append(
                (f"{formatted_hour}:{formatted_minute}", time_label)
            )
    return time_selection

class ResCompany(models.Model):
    _inherit = 'res.company'
    hour_work_start = fields.Selection(generate_time_selection(), string = "Hour Work Start", required=True, store=True, default="00:00")
    enable_split_shift = fields.Boolean(string="Customize", default=False)