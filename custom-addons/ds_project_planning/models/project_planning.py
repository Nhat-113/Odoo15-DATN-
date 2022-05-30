# -*- coding: utf-8 -*-

import json
from calendar import calendar
import string
from xml import dom
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
    employee_id_domain = fields.Char(
        compute="_compute_employee_id_domain",
        readonly=True,
        store=False,
    )
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    total_calendar_effort = fields.Float(
        string="Calendar Effort", compute="_compute_total_calendar_effort")
    total_estimate_effort = fields.Float(string="Estimate Effort")
    total_phase = fields.Integer(
        string="Total phases", compute="_count_phase_milestone")
    total_milestone = fields.Integer(
        string="Total milestones", compute="_count_phase_milestone")

    def _compute_task_total(self):
        for project in self:
            project.task_total = self.env['project.task'].search_count(['&',('issues_type','=',1),('project_id','=',project.id),('display_project_id','=',project.id),('active','=',True)])

    task_total = fields.Integer(compute='_compute_task_total')

    def _compute_total_calendar_effort(self):
        for project in self:
            total_effort = 0

            if len(project.planning_calendar_resources) > 0:
                for resource in project.planning_calendar_resources:
                    if resource.member_type:
                        total_effort += resource.calendar_effort * resource.member_type.rate / 100
                    else:
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

    @api.depends('planning_calendar_resources')
    def _compute_employee_id_domain(self):
        for project in self:
            user_ids = [
                user.id for user in project.planning_calendar_resources.employee_id]
            user_ids.append(self.env.user.employee_id.id)
            project.employee_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    @api.onchange('planning_calendar_resources')
    def _onchange_calendar_resources(self):
        # check the current user is the PM of this project
        # if self.user_id != self.env.user and not self.env.user.has_group('project.group_project_manager'):
        #     raise UserError(
        #         _('You are not the manager of this project, so you cannot assign members to it.'))

        # validate calendar resource duplicate
        if len(self.planning_calendar_resources) > 0:
            current_member_ids = [
                employee.employee_id.id for employee in self.planning_calendar_resources[:-1]]
            new_calendar_resource = self.planning_calendar_resources[-1]
            if new_calendar_resource.employee_id.id in current_member_ids:
                calendar_duplicate = list(filter(
                    lambda member: member.employee_id['id'] == new_calendar_resource.employee_id.id and
                    member.start_date <= new_calendar_resource.start_date and
                    member.end_date >= new_calendar_resource.start_date, self.planning_calendar_resources[:-1]))

                if len(calendar_duplicate) > 0:
                    for i in range(len(calendar_duplicate)):
                        if new_calendar_resource.start_date >= calendar_duplicate[i].start_date and new_calendar_resource.start_date <= calendar_duplicate[i].end_date:
                            raise ValidationError(
                                _('The project has duplicate members assigned in the range (%(start)s) to (%(end)s)!',
                                start=calendar_duplicate[i].start_date, end=calendar_duplicate[i].end_date))

        # update member_ids list
        user_ids = [
            user.user_id.id for user in self.planning_calendar_resources.employee_id]
        self.member_ids = self.env['res.users'].search(
            [('id', 'in', user_ids)])

    def _count_phase_milestone(self):
        for project in self:
            domain = [('project_id', '=', project.id)]
            num_phase = self.env['project.planning.phase'].search(domain)
            num_milestone = self.env['project.planning.milestone'].search(
                domain)

            project.total_phase = len(num_phase)
            project.total_milestone = len(num_milestone)

    @api.constrains('planning_calendar_resources')
    def _onchange_calendar(self):
        # check the current user is the PM of this project
        if self.user_id != self.env.user and not self.env.user.has_group('project.group_project_manager'):
            raise UserError(
                _('You are not the manager of this project, so you cannot assign members to it.'))

    def open_planning_task_all(self):
        for project in self:
            if self.env['project.task'].search_count(['&',('project_id','=',project.id),('issues_type','=',1)]) == 0:
                raise UserError(
                     _("No tasks found. Let's create one!"))
            else:
                action = self.with_context(active_id=self.id, active_ids=self.ids) \
                    .env.ref('ds_project_planning.open_planning_task_all_on_gantt') \
                    .sudo().read()[0]
            action['display_name'] = self.name
        return action