from datetime import date
from odoo import fields, models


class HistoryTaskScore(models.Model):
    _name = "history.task.score"
    _description = "History Task Score"

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', readonly=True)
    id_employee = fields.Integer(related='employee_id.employee_id', store=True)
    name = fields.Char(string='Employee', related='employee_id.name', store=True)
    department = fields.Many2one(related='employee_id.department_id', store=True)
    job = fields.Many2one(related='employee_id.job_id', store=True)
    year = fields.Integer(string="Year")
    task_score_avg = fields.Float(string='Task Score')

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
