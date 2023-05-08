from odoo import models, fields, api
from dateutil import tz
from datetime import date
import pandas as pd

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = "id desc"

    check_in = fields.Datetime(string="Check In", required=False)
    start = fields.Date(string="Start", store=True, compute='_compute_convert_datetime_start')
    end = fields.Date(string="End", store=True, compute='_compute_convert_datetime_end')

        
    
    @api.depends('check_in')
    def _compute_convert_datetime_start(self):
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
        for record in self:
            if bool(record.check_in):
                start = record.check_in.replace(tzinfo=tz.UTC)
                record.start = start.astimezone(local_tz)
            else:
                record.start = False
            
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
    
    
    def action_cron_update_attendance_checkout(self):
        if self.is_working_day(date.today()):
            pesudo_attendances = self.env['hr.attendance.pesudo'].search([('start', '=', date.today())])
            attendances = self.search([('start', '=', date.today()), ('check_out', '=', False)])
            for record in attendances:
                temp = pesudo_attendances.filtered(lambda p: p.employee_id.id == record.employee_id.id)
                if temp:
                    record.check_out = temp.check_out


    def is_working_day(self, date):
        return bool(len(pd.bdate_range(date, date)))
    
    
    #Override
    def unlink(self):
        dates = [d.start for d in self]
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
            start = record.check_in.replace(tzinfo=tz.UTC)
            end = record.check_out.replace(tzinfo=tz.UTC)
            record.start = start.astimezone(local_tz)
            record.end = end.astimezone(local_tz)
            if record.check_out and record.check_in:
                delta = record.check_out - record.check_in
                record.worked_hours = delta.total_seconds() / 3600.0
            else:
                record.worked_hours = False