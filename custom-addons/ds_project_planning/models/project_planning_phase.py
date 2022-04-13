# -*- coding: utf-8 -*-

from numpy import require
from odoo import models, fields, api
from datetime import date, datetime, time


class PlanningPhase(models.Model):
    """
    Describe Project Planning Phase in configuration.
    """
    _name = "project.planning.phase"
    _description = "Planning for Phase of project"
    _order = "sequence,id"
    _rec_name = "name"

    sequence = fields.Integer()
    name = fields.Char("Phase name", required=True, translate=True)
    start_date = fields.Date(string='Date Start', readonly=False, required=True, help="Start date of the phase",
                             default=lambda self: fields.Date.to_string(
                                 date.today().replace(day=1)))
    end_date = fields.Date(
        string='Date End', readonly=False, required=True, help="End date of the phase")
    description = fields.Char("Description", translate=True)
