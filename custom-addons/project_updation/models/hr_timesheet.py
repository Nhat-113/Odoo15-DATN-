from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'


    type_ot = fields.Selection([
        ('yes', 'OT'),
        ('no', 'Normal'),
    ], string='Type', index=True, copy=False, default='no', tracking=True, required=True)