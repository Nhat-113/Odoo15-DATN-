from datetime import date

from odoo import api, models, fields


class RampUp(models.Model):
    _inherit = ['hr.employee']
    _description = ''

    planning_calendar_resources = fields.One2many(
        'planning.calendar.resource', 'project_id', string='Planning Calendar Resources', readonly=True, compute='_get_calendar_resources')

    # project_task_score = fields.One2many(
    #     'project.task', 'project_id', string='Project Task', readonly=True, compute='_get_project_task')

    effort_rate_related = fields.Float(
        related='planning_calendar_resources.effort_rate')
    start_date_planning = fields.Date(
        related='planning_calendar_resources.start_date', store=True)
    end_date_planning = fields.Date(
        related='planning_calendar_resources.end_date', store=True)
    total_effort_rate = fields.Float(
        string='Total Effort Rate (%)', compute='get_effort_rate_total', store=True)
    task_score_avg = fields.Float(string='Task Score', digits=(
        12, 1), compute="_compute_avg_task_score_hr", default=0)

    def _compute_avg_task_score_hr(self):
        for employee in self:
            tasks = self.env['project.task'].search(
                ['&', '&', '&', '&', ('user_ids', 'in', employee.user_id.id), ('issues_type', '=', 1), 
                ('date_start', '>=', date(date.today().year, 1, 1)), 
                ('date_end', '<=', date(date.today().year, 12, 31)), ('task_score', 'not in', ['0'])])
            list_score = []
            for task in tasks:
                list_score.append(int(task.task_score))
            if len(list_score):
                employee.task_score_avg = round(sum(list_score)/len(list_score), 1)
            else:
                employee.task_score_avg = 0

    def _get_calendar_resources(self):
        for employee in self:
            employee.planning_calendar_resources = self.env['planning.calendar.resource'].search(
                [('employee_id', '=', employee.id)])

    # def _get_project_task(self):
    #     for employee in self:
    #         employee.project_task_score = self.env['project.task'].search(
    #             ['&', '&', '&', '&', ('user_ids', 'in', employee.user_id.id), ('issues_type', '=', 1), 
    #             ('date_start', '>=', date(date.today().year, 1, 1)), 
    #             ('date_end', '<=', date(date.today().year, 12, 31)), ('task_score', 'not in', ['0'])])

    def task_score_action(self):
        user_id = self.user_id.id
        name_view = self.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            'search_view_id': [self.env.ref('ds_ramp_up_recourse.task_score_search').id, 'search'],
            "res_model": "project.task",
            "views": [[self.env.ref('ds_ramp_up_recourse.task_score_view_tree').id, "tree"]],
            "domain": [('user_ids', 'in', user_id), ('issues_type', '=', 1), 
                ('date_start', '>=', date(date.today().year, 1, 1)), 
                ('date_end', '<=', date(date.today().year, 12, 31)), ('task_score', 'not in', ['0'])]
        }
        return action

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
