# -*- coding: utf-8 -*-

import json
from calendar import calendar
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time
from odoo.exceptions import UserError, ValidationError

class Project(models.Model):
    _inherit = ['project.project']

    privacy_visibility = fields.Selection(default='followers')
    planning_calendar_resources = fields.One2many(
        'planning.calendar.resource', 'project_id', string='Planning Calendar Resources', readonly=False)
    user_id_domain = fields.Char(
        compute="_compute_user_id_domain",
        readonly=True,
        store=False,
    )
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    total_calendar_effort = fields.Float(
        string="Calendar Effort", compute="_compute_total_calendar_effort")
    total_estimate_effort = fields.Float(string="Estimate Effort")

    def _compute_total_calendar_effort(self):
        for project in self:
            total_effort = 0

            if len(project.planning_calendar_resources) > 0:
                for resource in project.planning_calendar_resources:
                    total_effort += resource.calendar_effort
            project.total_calendar_effort = total_effort

    @api.depends('planning_calendar_resources')
    def _compute_user_id_domain(self):
        for project in self:
            user_ids = [
                user.user_id.id for user in project.planning_calendar_resources.employee_id]
            user_ids.append(self._uid)
            project.user_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    @api.onchange('planning_calendar_resources')
    def _onchange_calendar_resources(self):
        # check the current user is the PM of this project
        if self.user_id != self.env.user:
            raise UserError(_('You are not the manager of this project, so you cannot assign members to it.'))

        # update member_ids list
        user_ids = [
            user.user_id.id for user in self.planning_calendar_resources.employee_id]
        self.member_ids = self.env['res.users'].search(
            [('id', 'in', user_ids)])
