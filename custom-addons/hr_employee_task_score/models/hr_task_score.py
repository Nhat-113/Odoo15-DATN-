# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, tools


class HrEmployeeTaskScore(models.Model):
    _inherit = 'project.task.stage.personal'

    # project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)

    # _name = "hr.employee.task.score"
    # _description = "Hr Employee Task Score View"
    #
    # project_id = fields.Many2one('project.project', string="Project")
    # task_id = fields.Many2one('project.task.user.rel', string='Task Name')
    # user_id = fields.Many2one('res.users')
    # # task_score = fields.Selection('project.task')
    #
    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #     self.env.cr.execute("""
    #         create or replace VIEW task_score_tree_view AS
    #         select row_number() OVER () AS id, line.project_id, line.task_id, line.user_id from (
    #         select project_task.project_id, project_task_user_rel.task_id,
    #                project_task_user_rel.user_id
    #         from project_task
    #         inner join project_project ON (project_task.project_id=project_project.id)
    #         inner join project_task_user_rel ON (project_task.id = project_task_user_rel.task_id)) line
    #     """)

    # def _get_project_name(self):
    #     task_ids = self.env['project.task.user.rel'].search([('user_id', '=', self.id)])
    #     task = self.env['project.task'].search([])
    #     for item in task_ids:
    #         for k in task:
    #             if item.task_id == k.id:




    # name = fields.Char(string='Task Name', required=True)
    # project_name = fields.Char(string='Project Name')
    # task_score = fields.Selection([
    #     ('0', 'Nothing'),
    #     ('1', 'Very Bad'),
    #     ('2', 'Bad'),
    #     ('3', 'Normal'),
    #     ('4', 'Good'),
    #     ('5', 'Very Good'),
    # ], default='0', index=True, string="Task Score", tracking=True)
    # note = fields.Text(string='Description')

