# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.      
from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    task_score = fields.Char('project.task', compute="_compute_avg_task_score")

    @api.onchange('task_score')
    def _compute_avg_task_score(self):
        tasks = self.env['project.task'].search([])

        for employee in self:
            list_score = []
            for task in tasks:
                if employee.id in task.user_ids.ids:
                    list_score.append(int(task.task_score))
            if len(list_score):
                employee.task_score = str(round(sum(list_score)/len(list_score), 1))
            else:
                employee.task_score = 0

