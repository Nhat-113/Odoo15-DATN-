# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    task_score = fields.Float(string='Task Score', digits=(12, 1), compute="_compute_avg_task_score", default=0)

    @api.onchange('task_score')
    def _compute_avg_task_score(self):
        tasks = self.env['project.task'].search([])

        for employee in self:
            list_score = []
            for task in tasks:
                task.number_score = float(task.task_score)
                if employee.user_id.id in task.user_ids.ids:
                    list_score.append(int(task.task_score))
            if len(list_score):
                employee.task_score = round(sum(list_score)/len(list_score), 1)
            else:
                employee.task_score = 0

    def project_task_score_action(self):
        user_id = self.user_id.id
        name_view = 'Task Score/ ' + self.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            'search_view_id': [self.env.ref('hr_employee_task_score.view_task_score_search').id, 'search'],
            "res_model": "project.task",
            "views": [[self.env.ref('hr_employee_task_score.project_task_score_view_tree').id, "tree"]],
            "domain": [('user_ids', 'in', user_id)]
        }
        return action


class ProjectTask(models.Model):
    _inherit = 'project.task'

    number_score = fields.Float('Number Score', digits=(12, 1), group_operator='avg')
