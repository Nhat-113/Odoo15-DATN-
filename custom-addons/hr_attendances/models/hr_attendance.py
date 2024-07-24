from odoo import models, fields, api
from dateutil import tz
from datetime import date, time, timedelta
import pandas as pd
import pytz

def extract_hour_minute(time_string):
    try:
        hour, minute = time_string.split(":")
        return int(hour), int(minute)
    except ValueError:
        raise ValueError("Invalid time format. Expected 'HH:MM'.")
        
class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = "id desc"

    check_in = fields.Datetime(string="Check In", default=fields.Datetime.now, required=False)
    start = fields.Date(string="Start", store=True, compute='_compute_convert_datetime_start')
    end = fields.Date(string="End", store=True, compute='_compute_convert_datetime_end')
    status = fields.Selection([('early', 'Early'),
                             ('timely', 'Timely'),
                             ('late', 'Late')] ,
                            string="Status", 
                            store=True,
                            compute='_compute_convert_datetime_start')
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
        specific_time_start = time(hour_start, minute_start, 0)
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
    
    @api.depends('check_in')
    def _compute_convert_datetime_start(self):
        local_tz = tz.gettz(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        utc_tz = pytz.timezone(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        for record in self:
            if bool(record.check_in):
                start = record.check_in.replace(tzinfo=tz.UTC)
                record.start = start.astimezone(local_tz)
            else:
                record.start = False
            if record.check_in:
                checkin_tz = pytz.utc.localize(record.check_in).astimezone(utc_tz)
                if checkin_tz.hour == 8 and checkin_tz.minute < 30 or checkin_tz.hour < 8:
                    record.status = 'early'
                elif checkin_tz.hour == 8 and checkin_tz.minute == 30:
                    record.status = 'timely'
                else:
                    record.status = 'late'
            
    @api.depends('check_out')
    def _compute_convert_datetime_end(self):
        local_tz = tz.gettz(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        for record in self:
            if bool(record.check_out):
                end = record.check_out.replace(tzinfo=tz.UTC)
                record.end = end.astimezone(local_tz)
            else:
                record.end = False

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        # TODO create check validity func here
        return True

    def is_working_day(self, date):
        return bool(len(pd.bdate_range(date, date)))
    
    
    #Override
    def unlink(self):
        date_min = ""
        date_max = ""
        date_start = [d.start for d in self if d.start]
        date_end = [d.end for d in self if d.end]
        if date_start:
            date_min = min(date_start)
            date_max = max(date_start)
        
        elif date_end:
            date_min = min(date_end)
            date_max = max(date_end)
        
        pesudos = self.env['hr.attendance.pesudo'].search([
            ('employee_id', 'in', self.employee_id.ids),
            ('location_date', '>=', date_min),
            ('location_date', '<=', date_max)])
        pesudos.unlink()
        
        return super(HrAttendance, self).unlink()

    @api.constrains('check_in', 'check_out')
    def _change_pesudo_data(self):
        changed_record = self.env['hr.attendance.pesudo'].search([
            ('employee_id', '=', self.employee_id.id), 
            '|',
            ('check_in', '=', self.check_in),
            ('check_out', '=', self.check_out)
        ])

        changed_record.update({
            "check_in": self.check_in,
            "check_out": self.check_out
        })


class HrAttendancePesudo(models.Model):
    _name = 'hr.attendance.pesudo'
    _order = "id desc"
    
    employee_id = fields.Many2one('hr.employee', string="Employee")
    start = fields.Date(string="Start", store=True, compute='_compute_convert_datetime')
    end = fields.Date(string="End", store=True, compute='_compute_convert_datetime')
    check_in = fields.Datetime(string="Check In")
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(string='Worked Hours', compute='_compute_convert_datetime', store=True, readonly=True)
    
    
    
    @api.depends('check_in', 'check_out')
    def _compute_convert_datetime(self):
        local_tz = tz.gettz(self.env.user.tz or 'Asia/Ho_Chi_Minh')
        for record in self:
            if record.check_out and record.check_in:
                start = record.check_in.replace(tzinfo=tz.UTC)
                end = record.check_out.replace(tzinfo=tz.UTC)
                record.start = start.astimezone(local_tz)
                record.end = end.astimezone(local_tz)

                delta = record.check_out - record.check_in
                record.worked_hours = delta.total_seconds() / 3600.0
            else:
                record.worked_hours = False
                record.start = False
                record.end = False
