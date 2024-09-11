from odoo import api, fields, models

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

class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    hour_work_start = fields.Selection(generate_time_selection(), string = "Hour Work Start", required=True, default="00:00")
    enable_split_shift = fields.Boolean(string="Customize", default=False)
    remove_lunch_break = fields.Boolean(string="Lunch Break", default=False)
    
    @api.model
    def get_values(self):
        res = super(ResConfigSetting, self).get_values()
        company = self.env.company
        res.update({
            'hour_work_start': company.hour_work_start,  
            'enable_split_shift': company.enable_split_shift,
            'remove_lunch_break': company.remove_lunch_break
        })
        return res

    def set_values(self):
        super(ResConfigSetting, self).set_values()
        company = self.env.company

        fields_to_check = ['hour_work_start', 'enable_split_shift', 'remove_lunch_break']
        
        for field in fields_to_check:
            if self[field] != company[field]:
                company.write({field: self[field]})
