from datetime import date
from odoo import fields, models


class CurrentTaskScore(models.Model):
    _name = "current.task.score"
    _description = "Current Task Score"
    _auto = False

    id_current = fields.Many2one('hr.employee', string="ID", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    name = fields.Char(string="Employee Name", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    job_id = fields.Many2one('hr.job', string="Job Position", readonly=True)
    parent_id = fields.Many2one('hr.employee', string="Parent ID", readonly=True)
    task_score_avg = fields.Float(string='Task Score', digits=(12, 1), readonly=True)


    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                (
                    SELECT
                        emp.id,
                        emp.id as employee_id,
                        emp.name,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id,
						SUM(project_task.task_score::decimal)/COUNT(project_task.task_score) as task_score_avg
						
                    FROM (
                        SELECT
                            id,
                            name,
                            department_id,
                            job_id,
                            parent_id,
							user_id
                        FROM
                            hr_employee
                        ) as emp
                    LEFT JOIN 	
                        project_task_user_rel ab
                            ON ab.user_id = emp.user_id
					LEFT JOIN
                        project_task
                            ON ab.task_id = project_task.id
					WHERE
						project_task.date_start >= CONCAT(to_char(date_part('year', CURRENT_DATE), '9999'), '-01-01')::date
						AND project_task.date_end <= CONCAT(to_char(date_part('year', CURRENT_DATE), '9999'), '-12-31')::date
						AND project_task.issues_type = 1
						AND project_task.task_score != '0'
					GROUP BY
						emp.id,
                        emp.name,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id
                )
            )
        """ % (self._table))

    def current_task_score_action(self):
        user_id = self.env['hr.employee'].search([('id', '=', self.id)]).user_id.id
        name_view = self.env['hr.employee'].search([('id', '=', self.id)]).name
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


