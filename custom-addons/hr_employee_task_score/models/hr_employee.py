# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from builtins import print, set

from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    task_score = fields.Char(string='Task Score', compute="_compute_avg_task_score")

    @api.onchange('task_score')
    def _compute_avg_task_score(self):
        tasks = self.env['project.task'].search([])

        for employee in self:
            list_score = []
            for task in tasks:
                if employee.user_id.id in task.user_ids.ids:
                    list_score.append(int(task.task_score))
            if len(list_score):
                employee.task_score = round(sum(list_score)/len(list_score), 1)
                if employee.task_score == '0.0':
                    employee.task_score = '0'
            else:
                employee.task_score = '0'

    def project_task_score_action(self):
        user_id = self.user_id.id
        name_view = 'Task Score/ ' + self.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "views": [[self.env.ref('hr_employee_task_score.project_task_score_view_tree').id, "tree"]],
            "domain": [('user_ids', 'in', user_id)]
        }
        return action

