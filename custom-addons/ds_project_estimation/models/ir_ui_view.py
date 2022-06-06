from odoo import models, fields


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[('rs_plan_gantt', "Resource Planning Gantt")], ondelete={'rs_plan_gantt': 'cascade'})
