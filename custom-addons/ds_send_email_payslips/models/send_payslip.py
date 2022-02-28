from odoo import models, _, fields
from odoo.exceptions import UserError


class SendPayslips(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    def send_payslip(self):
        """
        This function opens a window to compose an email, with the edi payslip template message loaded by default
        """
        self.ensure_one()
        try:
            template = self.env.ref(
                'ds_send_email_payslips.email_template_hr_payslip', False)
        except ValueError:
            template = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = dict(
            default_model='hr.payslip',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
        )

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def _send_multi_payslips(self):
        template = self.env.ref(
            'ds_send_email_payslips.email_template_hr_payslip', raise_if_not_found=False)
        if not template:
            raise UserError(
                _('Template "ds_send_email_payslips.email_template_hr_payslip" was not found. No email has been sent. Please contact an administrator to fix this issue.'))

        for rec in self:
            template.send_mail(
                rec.id,
                force_send=True
            )
            message_id = self.env['ds_send_email_payslips.message.wizard'].create(
                {'message': _("Email Payslips is successfully sent")})

            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ds_send_email_payslips.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread']

    def send_multi_payslips(self):
        template = self.env.ref(
            'ds_send_email_payslips.email_template_hr_payslip', raise_if_not_found=False)
        if not template:
            raise UserError(
                _('Template "ds_send_email_payslips.email_template_hr_payslip" was not found. No email has been sent. Please contact an administrator to fix this issue.'))

        if self.slip_ids:
            for rec in self.slip_ids:
                template.send_mail(
                    rec.id,
                    force_send=True
                )
            message_id = self.env['ds_send_email_payslips.message.wizard'].create(
                {'message': _("Email Payslips is successfully sent")})

            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ds_send_email_payslips.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }
