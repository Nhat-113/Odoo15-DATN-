# -*- coding:utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.company"
    _description = 'Res Partner Director'

    representative = fields.Char(string="Representative")
    position = fields.Char(string="Position")
