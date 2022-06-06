from odoo import models, fields


class IrActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[('rs_plan_gantt', "Resource Planning Gantt")], ondelete={'rs_plan_gantt': 'cascade'})
