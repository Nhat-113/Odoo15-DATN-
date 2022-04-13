# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json


class ProjectTask(models.Model):
    _inherit = ['project.task']

    user_id_domain = fields.Char(
        related='project_id.user_id_domain',
        readonly=True,
        store=False,
    )
