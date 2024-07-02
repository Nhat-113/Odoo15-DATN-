from odoo import models, fields, api
from dateutil import tz
from datetime import date
import pandas as pd
import pytz

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


    @api.depends('check_in', 'check_out')
    def _compute_location_date(self):
        user_tz = pytz.timezone(self.env.user.tz)
        for record in self:
            if record.check_in:
                record.location_date = record.check_in.astimezone(user_tz).date()
            elif not record.check_in and record.check_out:
                record.location_date = record.check_out.astimezone(user_tz).date()
            else:
                record.location_date = None
    
    @api.depends('check_in')
    def _compute_convert_datetime_start(self):
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
        utc_tz = pytz.timezone('Asia/Ho_Chi_Minh')
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
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
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
    
    def action_cron_batch_verify_data(self):
        ################################
        # verify all records missing checkout
        ################################
        attendance_update_failed = self.env['hr.attendance'].sudo().search([('check_out', '=', False)])
        if attendance_update_failed:
            dates = [att.start for att in attendance_update_failed]
            date_min = min(dates)
            date_max = max(dates)
            attendance_pseudo = self.env['hr.attendance.pesudo'].sudo().search([('employee_id', 'in', attendance_update_failed.employee_id.ids),
                                                                                ('start', '>=', date_min),
                                                                                ('start', '<=', date_max)])
            for record in attendance_update_failed:
                att_pseudo = attendance_pseudo.filtered(lambda x: x.employee_id.id == record.employee_id.id and x.start == record.start)
                if att_pseudo:
                    max_time = max([att.check_out for att in att_pseudo])
                    if record.check_in <= max_time:
                        record.check_out = max_time
                else:
                    record.check_out = record.check_in


    def is_working_day(self, date):
        return bool(len(pd.bdate_range(date, date)))
    
    
    #Override
    def unlink(self):
        dates = [d.start for d in self if d.start]
        date_min = min(dates)
        date_max = max(dates)
        pesudos = self.env['hr.attendance.pesudo'].search([('employee_id', 'in', self.employee_id.ids), 
                                                 ('start', '>=', date_min),
                                                 ('start', '<=', date_max)])
        pesudos.unlink()
        return super(HrAttendance, self).unlink()

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
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
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
