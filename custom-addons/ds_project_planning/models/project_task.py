# -*- coding: utf-8 -*-

from cmath import phase
from odoo import models, fields, api
import json


class ProjectTask(models.Model):
    _inherit = ['project.task']

    user_id_domain = fields.Char(
        related='project_id.user_id_domain',
        readonly=True,
        store=False,
    )
    phase_id = fields.Many2one(
        'project.planning.phase', string='Phase', required=False, help="Project Phase")
    milestone_id = fields.Many2one(
        'project.planning.milestone', string='Milestone', required=False, domain=[('phase_id', '=', phase_id)], help="Project Milestone")

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'date_start' in vals or 'date_end' in vals:
            domain_normal = ['&', '&', ('project_id', '=', self.project_id.id), (
                'start_date', '<=', self.date_start), ('end_date', '>=', self.date_end)]
            domain_exception = ['&', '&', ('project_id', '=', self.project_id.id), (
                'start_date', '<=', self.date_end), ('end_date', '>=', self.date_end)]
            phase_id = self.env['project.planning.phase'].search(domain_normal)
            milestone_id = self.env['project.planning.milestone'].search(
                domain_normal)
            phase_id_exception = self.env['project.planning.phase'].search(
                domain_exception)
            milestone_id_exception = self.env['project.planning.milestone'].search(
                domain_exception)
            task_phase_id, task_milestone_id = False, False

            if phase_id:
                task_phase_id = phase_id.id
            elif phase_id_exception:
                task_phase_id = phase_id_exception.id

            if milestone_id:
                task_milestone_id = milestone_id.id
            elif milestone_id_exception:
                task_milestone_id = milestone_id_exception.id

            self.write({'phase_id': task_phase_id,
                        'milestone_id': task_milestone_id})

        return res
