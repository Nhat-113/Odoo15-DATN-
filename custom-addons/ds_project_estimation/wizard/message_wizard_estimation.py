from odoo import fields, models, _


class EstimationMessageWizard(models.TransientModel):
    _name = 'estimation.message.wizard'
    _description = "Show Message Success"

    message = fields.Text('Message', required=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}