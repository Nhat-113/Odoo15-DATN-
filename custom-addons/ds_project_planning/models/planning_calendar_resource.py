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

    _sql_constraints = [
        ('project_id_employee_id_uniq', 'unique(project_id,employee_id)',
         'The project has duplicate members assigned to it!')
    ]

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for resource in self:
            if resource.end_date and resource.start_date:
                delta = resource.end_date - resource.start_date
                resource.duration = delta.days if delta.days > 0 else 1

    @api.depends('duration', 'calendar_effort')
    def _compute_effort_rate(self):
        """ Calculates effort rate (%)"""
        for resource in self:
            if resource.duration != 0:
                resource.effort_rate = resource.calendar_effort * 20 / resource.duration

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
