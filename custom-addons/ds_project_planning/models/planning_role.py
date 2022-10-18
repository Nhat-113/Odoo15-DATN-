# -*- coding: utf-8 -*-
from odoo import models, fields
from random import randint

class PlanningRoles(models.Model):
    """ Roles of member in project planning """
    _name = "planning.roles"
    _description = "Project Planning Roles"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Name', required=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    company_id = fields.Many2one('res.company', string='Company', required=False, readonly=False,
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Role name already exists!"),
    ]