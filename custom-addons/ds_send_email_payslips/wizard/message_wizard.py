from odoo import fields, models, _


class SendPayslipMessageWizard(models.TransientModel):
    _name = 'ds_send_email_payslips.message.wizard'
    _description = "Show Message Success"

    message = fields.Text('Message', required=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}
