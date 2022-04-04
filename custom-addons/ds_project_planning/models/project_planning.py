# -*- coding: utf-8 -*-

from numpy import require
from odoo import models, fields, api
from datetime import date, datetime, time


class Project(models.Model):
    _inherit = ['project.project']


# class Planning(models.Model):
#     _name = "project.planning"
#     # _inherit = ["project"]
#     _description = "Project Planning"

#     project_name = fields.Char("Project Name", required=True)
#  
