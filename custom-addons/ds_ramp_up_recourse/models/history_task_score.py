from datetime import date
from odoo import fields, models


class HistoryTaskScore(models.Model):
    _name = "history.task.score"
    _description = "History Task Score"

    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    name = fields.Char(string='Employee', related='employee_id.name', store=True)
    department_id = fields.Many2one('hr.department',related='employee_id.department_id', string="Department", readonly=True)
    job_id = fields.Many2one('hr.job',related='employee_id.job_id', string="Job Position", readonly=True)
    parent_id = fields.Many2one('hr.employee',related='employee_id.parent_id', string="Parent ID", readonly=True)
    company_id = fields.Many2one('res.company',related='employee_id.company_id', string="Company ID", readonly=True)
    year = fields.Integer(string="Year", readonly=True)
    task_score_avg = fields.Float(string='Task Score', digits=(12, 1), readonly=True)

    def _get_project_task(self):
        for employee in self.employee_id:
            employee.project_task_score = self.env['project.task'].search(
                ['&', '&', '&', ('user_ids', 'in', employee.user_id.id), ('issues_type', '=', 1),
                 ('date_start', '<', date(date.today().year, 1, 1)),
                 ('task_score', 'not in', ['0'])])

    def get_history_task_score(self):
        employees = self.env['hr.employee'].search([])
        for emp in employees:
            tasks = self.env['project.task'].search(
                ['&', '&', '&', '&', ('user_ids', 'in', emp.user_id.id), ('issues_type', '=', 1),
                ('date_start', '>=', date(date.today().year - 1, 1, 1)),
                ('date_end', '<=', date(date.today().year - 1, 12, 31)),
                ('task_score', 'not in', ['0'])])
            list_score = []
            for task in tasks:
                list_score.append(int(task.task_score))
            if len(list_score):
                task_score_avg = round(sum(list_score)/len(list_score), 1)
            else:
                task_score_avg = 0
            self.create({
                'employee_id': emp.id,

                'year': date.today().year - 1,
                'task_score_avg': task_score_avg
            })

        return

    def history_task_score_action(self):
        user_id = self.employee_id.user_id.id
        name_view = self.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            'search_view_id': [self.env.ref('ds_ramp_up_recourse.task_score_search').id, 'search'],
            "res_model": "project.task",
            "views": [[self.env.ref('ds_ramp_up_recourse.task_score_view_tree').id, "tree"]],
            "domain": [('user_ids', 'in', user_id), ('issues_type', '=', 1), 
                ('date_start', '>=', date(self.year, 1, 1)), 
                ('date_end', '<=', date(self.year, 12, 31)), ('task_score', 'not in', ['0'])]
        }
        return action
