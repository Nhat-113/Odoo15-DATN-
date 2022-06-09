from datetime import date

from odoo import api, models, fields


class RampUp(models.Model):
    _inherit = ['hr.employee']
    _description = ''

    planning_calendar_resources = fields.One2many(
        'planning.calendar.resource', 'project_id', string='Planning Calendar Resources', readonly=True, compute='_get_calendar_resources')

    effort_rate_related = fields.Float(
        related='planning_calendar_resources.effort_rate')
    start_date_planning = fields.Date(
        related='planning_calendar_resources.start_date', store=True)
    end_date_planning = fields.Date(
        related='planning_calendar_resources.end_date', store=True)
    total_effort_rate = fields.Float(
        string='Total Effort Rate (%)', compute='get_effort_rate_total', store=True)

    def _get_calendar_resources(self):
        for employee in self:
            employee.planning_calendar_resources = self.env['planning.calendar.resource'].search(
                [('employee_id', '=', employee.id)])

    @api.model
    @api.depends('effort_rate_related')
    def get_effort_rate_total(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            planning_calendars = self.env['planning.calendar.resource'].search(
                ['&', '&', ('employee_id', '=', employee.id), ('start_date', '<=', date.today()), ('end_date', '>=', date.today())])
            total = 0
            for planning_calendar in planning_calendars:
                total += planning_calendar.effort_rate
            employee.total_effort_rate = total


class CalendarResource(models.Model):
    _inherit = ['planning.calendar.resource']
    _description = ''

    actual_effort_rate = fields.Float(
        string='Actual Effort', compute='_get_actual_effort')
    estimation_effort_rate = fields.Float(
        string='Estimation Effort', compute='_get_estimate_effort_total')

    def _get_actual_effort(self):
        for calendar in self:
            timesheet_source = self.env['account.analytic.line'].search(
                ['&', ('project_id', '=', calendar.project_id.id), ('employee_id', '=', calendar.employee_id.id)])
            employee_unit_amount = [x.unit_amount for x in timesheet_source]
            total = 0
            for unit_amount in employee_unit_amount:
                total += unit_amount
            calendar.actual_effort_rate = round(total/8/20, 2)

    def _get_estimate_effort_total(self):
        for calendar in self:
            tasks = self.env['project.task'].search(
                [('project_id', '=', calendar.project_id.id)])
            total = 0
            for task in tasks:
                if calendar.employee_id.user_id.id in task.user_ids.ids:
                    total += task.planned_hours
            calendar.estimation_effort_rate = round(total/8/20, 2)
