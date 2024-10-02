from odoo import models, fields, api
from datetime import date, time, timedelta
import pytz

def extract_hour_minute(time_string):
    try:
        hour, minute = time_string.split(":")
        return int(hour), int(minute)
    except ValueError:
        raise ValueError(_("Invalid time format. Expected 'HH:MM'."))
        
class HrAttendancePseudo(models.Model):
    _inherit = "hr.attendance.pesudo"
    
    
    attendance_device_details = fields.One2many('attendance.device.details', 'pseudo_attendance_id', string="Attendance Device Details")
    attendance_device_details_app = fields.One2many('attendance.device.details.app', 'pseudo_attendance_id_app', string="Attendance Device Details App")
    is_multiple = fields.Boolean(string="Multiple")
    location_date = fields.Date("Location Date", store=True, compute="_compute_location_date")
    location_date_multi = fields.Date("Location Date", store=True, compute="_compute_location_date_multi")
    
    @api.depends('check_in', 'check_out')
    def _compute_location_date(self):
        user_tz = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        for record in self:
            if record.check_in:
                record.location_date = record.check_in.astimezone(user_tz).date()
            elif not record.check_in and record.check_out:
                record.location_date = record.check_out.astimezone(user_tz).date()
            else:
                record.location_date = None
    @api.depends('check_in', 'check_out')
    def _compute_location_date_multi(self):
        user_tz = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        company = self.employee_id.company_id
        hour_start, minute_start = extract_hour_minute(company.hour_work_start or company[0].hour_work_start)
        specific_time_start = time(hour_start, minute_start)
        for record in self:
            if record.check_in:
                user_check_in = pytz.utc.localize(record.check_in).astimezone(user_tz)
                if user_check_in.time() < specific_time_start:
                    user_check_in = user_check_in.date() - timedelta(days=1)
                else :
                    user_check_in = user_check_in.date()
                record.location_date_multi = user_check_in
            elif not record.check_in and record.check_out:
                user_check_out = pytz.utc.localize(record.check_out).astimezone(user_tz)
                if user_check_out.time() < specific_time_start:
                    user_check_out = user_check_out.date() - timedelta(days=1)
                else:
                    user_check_out = user_check_out.date()
                record.location_date_multi = user_check_out
            else:
                record.location_date_multi = None
                
    def unlink(self):
        self.attendance_device_details.unlink()
        return super(HrAttendancePseudo, self).unlink()