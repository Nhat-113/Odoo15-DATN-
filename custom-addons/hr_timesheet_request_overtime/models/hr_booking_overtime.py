
from odoo import api, fields, models
import pandas as pd


class HrBookingOvertime(models.Model):
    _name = "hr.booking.overtime"

    request_overtime_id = fields.Many2one('hr.request.overtime', string='Booking Overtime', readonly=False)
    
    employee_id = fields.Many2one(
        'hr.employee', string='Member Name', required=True, help="Member name")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working overtime on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished overtime on project")

    duration = fields.Integer(compute='_compute_duration', string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=1)

    booking_time_overtime = fields.Integer(string="Plan Overtime",
                              readonly=False, help="The booking of working overtime in the project", default=False)

    actual_overtime = fields.Integer(string="Actual Overtime",
                              readonly=False, help="The duration actual of working overtime in the project", default=1)
    
    inactive = fields.Boolean(string="Inactive Member", default=False, store=True)
    description = fields.Text("Description", translate=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for record in self:
            if record.inactive == False:
                if record.end_date and record.start_date:
                    working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                    record.end_date.strftime('%Y-%m-%d')))
                    record.duration = working_days if working_days > 0 else 1
                else:
                    record.duration = 1
            else:
                if record.start_date and record.inactive_date:
                    working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                    record.inactive_date.strftime('%Y-%m-%d')))
                    record.duration = working_days if working_days > 0 else 1
                else:
                    record.duration = 1

    def action_view_timesheet_overtime(self):
        print('-----------------------------------')