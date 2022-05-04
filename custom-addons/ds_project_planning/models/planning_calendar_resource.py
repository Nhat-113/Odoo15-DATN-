# -*- coding: utf-8 -*-

from calendar import calendar
from email.policy import default
from attr import field
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class PlanningCalendarResource(models.Model):
    _name = "planning.calendar.resource"
    _description = "Planning Calendar Resource Of Project"
    _order = "start_date desc"
    _rec_name = "employee_id"

    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Member Name', required=True, help="Member name")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished working on project")
    duration = fields.Integer(compute='_compute_duration', string="Duration",
                              readonly=True, help="The duration of working time in the project", default=1)
    calendar_effort = fields.Float(string="Calendar Effort", default=1.0)
    effort_rate = fields.Float(string="Effort Rate", compute='_compute_effort_rate',
                               readonly=True, help="Effort Rate (%) = Calendar Effort * 20 / Duration")
    role_ids = fields.Many2many('planning.roles', string='Roles')
    note = fields.Text(string='Note')
    member_type = fields.Many2one(
        'planning.member.type', string="Member Type")
    member_type_rate = fields.Float(
        related='member_type.rate', string="Member Type (%)")
    inactive = fields.Boolean(string="Inactive Member",
                              default=False, store=True)
    inactive_date = fields.Date(string='Inactive Date', help="The start date of the member's inactivity in the project.",
                                default=fields.Date.today)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for resource in self:
            if resource.end_date and resource.start_date:
                delta = resource.end_date - resource.start_date
                resource.duration = delta.days if delta.days > 0 else 1
            else:
                resource.duration = 1

    @api.depends('duration', 'calendar_effort')
    def _compute_effort_rate(self):
        """ Calculates effort rate (%)"""
        for resource in self:
            if resource.duration != 0:
                resource.effort_rate = resource.calendar_effort * 20 / resource.duration * 100

    def _check_dates(self):
        for resource in self:
            if resource.end_date and resource.start_date > resource.end_date:
                raise ValidationError(_(
                    'Member %(resource)s: start date (%(start)s) must be earlier than end date (%(end)s).',
                    resource=resource.employee_id.name, start=resource.start_date, end=resource.end_date,
                ))

    @api.constrains('start_date', 'end_date')
    def _check_start_end(self):
        return self._check_dates()

    @api.constrains('inactive', 'inactive_date')
    def _unassign_member_in_tasks (self):
        if self.inactive:
            inactive_date = fields.Datetime.to_datetime(self.inactive_date)

            tasks = self.env['project.task'].search(['&', '&', ('project_id', '=', self.project_id.id), ('user_ids', 'in', self.employee_id.user_id.id), ('date_start', '>=', inactive_date)])
            for task in tasks:
                user_ids = [x for x in task.user_ids.ids if x != self.employee_id.user_id.id]
                task.write({'user_ids': [(6, 0, user_ids)]})
            
    @api.model
    def open_calendar_resource(self, project_id):
        target_project = self.env['project.project'].browse(project_id)

        return {
            "name": _("Calendar Resource (%s)", target_project.name),
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "views": [[self.env.ref('ds_project_planning.view_form_calendar_resource').id, "form"]],
            "target": "new",
            "res_id": project_id
        }


class PlanningAllocateEffortRate(models.Model):
    """ Type of member in project planning """
    _name = "planning.member.type"
    _description = "Member Type of Project"
    _rec_name = "name"

    name = fields.Char('Name', required=True)
    rate = fields.Float(string='Rate', default=50.0)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Member Type name already exists!"),
    ]
