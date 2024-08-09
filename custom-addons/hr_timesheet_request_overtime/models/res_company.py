# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    timeoff_type_overtime = fields.Many2one('hr.leave.type', string="Timeoff type", domain="[('requires_allocation', '=', 'yes'), ('active', '=', True)]")