# -*- coding: utf-8 -*-

from numpy import require
from odoo import models, fields, api
from datetime import date, datetime, time

class PlanningCalendarResource(models.Model):
    _name = "planning.calendar.resource"
    _description = "Planning Calendar Resource Of Project"
    _order = "start_date desc"
    _rec_name = "employee_id"

    project_id = fields.Many2one(
        'project.project', string='Project', required=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Member Name', required=True, help="Member name")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working on project",
                             default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished working on project")