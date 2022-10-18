# -*- coding: utf-8 -*-
from odoo import api, models, fields
from random import randint
from odoo.exceptions import UserError

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
        ('name_uniq', 'Check(1=1)', "Role name already exists!"),
    ]

    @api.constrains('name', 'company_id')
    def check_duplica_name(self):
        for record in self:
            name_dupli = self.env['planning.roles'].search([('name', '=', record.name), ('company_id', '=', record.company_id.id), ('id', '!=', record.id)])
            if len(name_dupli) > 0:
               raise UserError('Role name already exists!')