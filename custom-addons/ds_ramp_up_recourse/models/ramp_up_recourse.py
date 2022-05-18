from re import search

from lxml.html.diff import token

from odoo import models, fields
from odoo.service.server import empty_pipe


class RampUp(models.Model):
    _inherit = ['hr.employee']
    _description = ''

    planning_calendar_resources = fields.One2many(
        'planning.calendar.resource', 'project_id', string='Planning Calendar Resources', readonly=True, compute='_get_calendar_resources')
    timesheet_source = fields.One2many(
        'account.analytic.line', string='Timesheet Hour Spent', readonly=True, compute='_get_timesheet_amount')

    total_effort_rate = fields.Float(string='Total Effort Rate (%)', compute='_get_effort_rate_total', store=True)
    total_calendar_effort_rate = fields.Float(string='Calendar Effort', compute='_get_calendar_effort_rate_total')
    actual_effort_rate = fields.Float(string='Actual Effort', compute='_get_actual_effort')
    estimation_effort_rate = fields.Float(string='Estimation Effort', compute='_get_estimate_effort_total')
    
    def _get_calendar_resources(self):
        for employee in self:
            employee.planning_calendar_resources = self.env['planning.calendar.resource'].search([('employee_id', '='
                                                                                                   , employee.id)])

    def _get_effort_rate_total(self):
        for employee in self:
            effort_rates = [x.effort_rate for x in employee.planning_calendar_resources]
            total = 0
            for effort_rate in effort_rates:
                total += effort_rate
            employee.total_effort_rate = total
        
    def _get_calendar_effort_rate_total(self):
        for employee in self:
            calendar_rates = [x.calendar_effort for x in employee.planning_calendar_resources]
            total = 0
            for calendar_rate in calendar_rates:
                total += calendar_rate
            employee.total_calendar_effort_rate = total

    def _get_timesheet_amount(self):
        for employee in self:
            employee.timesheet_source = self.env['account.analytic.line'].search([('employee_id', '=', employee.id)])

    def _get_actual_effort(self):
        for employee in self:
            employee_unit_amount = [x.unit_amount for x in employee.timesheet_source]
            total = 0
            for unit_amount in employee_unit_amount:
                total += unit_amount
            employee.actual_effort_rate = round(total/8/20, 2)

    def _get_estimate_effort_total(self):
        tasks = self.env['project.task'].search([])

        for employee in self:
            total = 0
            for task in tasks:
                if employee.user_id.id in task.user_ids.ids:
                    total += task.planned_hours
            employee.estimation_effort_rate = round(total/8/20)
