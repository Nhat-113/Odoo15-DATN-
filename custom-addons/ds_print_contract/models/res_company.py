# -*- coding:utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.company"
    _description = 'Res Partner Director'

    representative = fields.Char(string="Representative", required=True)
    position = fields.Char(string="Position", required=True)
    user_email = fields.Char(string="Email", required=True)
