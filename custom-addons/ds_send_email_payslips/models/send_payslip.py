from odoo import models, _, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, datetime
import time
from ast import literal_eval


class SendPayslips(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    email_send_status = fields.Selection([
        ('not_sent_yet', 'Not sent yet'),
        ('sent', 'Sent'),
    ], string='Email Send Status', readonly=True,
        tracking=True, help='Indicates this payslip has sent to the employee by email or not', default='not_sent_yet')

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

        if self.employee_id.id != self.env.user.employee_id.id:
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
        else:
            template.send_mail(self.id, force_send=True)
            self.write({'email_send_status': 'sent'})
            message_id = self.env['ds_send_email_payslips.message.wizard'].create(
                {'message': _("Email Payslip is successfully sent")})

            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ds_send_email_payslips.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }

    def send_payslip_cron(self):
        template = self.env.ref(
            'ds_send_email_payslips.email_template_hr_payslip', raise_if_not_found=False)

        if template:
            payslip_ids = self.env['ir.config_parameter'].sudo(
            ).get_param('payslip_send_mail_cron.records')
            payslips = self.env['hr.payslip'].browse(literal_eval(payslip_ids))

            for rec in payslips:
                template.send_mail(
                    rec.id,
                    force_send=True
                )

            # change send mail status
            payslips.write({'email_send_status': 'sent'})

        # Reset global variable
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip_send_mail_cron.records', [])

        return {}

    def _send_multi_payslips(self):
        template = self.env.ref(
            'ds_send_email_payslips.email_template_hr_payslip', raise_if_not_found=False)
        if not template:
            raise UserError(
                _('Template "ds_send_email_payslips.email_template_hr_payslip" was not found. No email has been sent. Please contact an administrator to fix this issue.'))

        # set global variable for self' records
        self.env['ir.config_parameter'].sudo().set_param(
            'payslip_send_mail_cron.records', self.ids)

        # Execute cron job after 5s
        ir_cron = self.env.ref('ds_send_email_payslips.payslip_send_mail_cron')
        ir_cron.write(
            {'active': True, 'nextcall': fields.datetime.now() + timedelta(seconds=5)})

        time.sleep(1)
        message_id = self.env['ds_send_email_payslips.message.wizard'].create(
            {'message': _("In the next few minutes, email payslips will be sent to employees.")})

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
            # set global variable for self' records
            self.env['ir.config_parameter'].sudo().set_param(
                'payslip_send_mail_cron.records', self.slip_ids.ids)

            # Execute cron job after 5s
            ir_cron = self.env.ref(
                'ds_send_email_payslips.payslip_send_mail_cron')
            ir_cron.write(
                {'active': True, 'nextcall': fields.datetime.now() + timedelta(seconds=5)})

            time.sleep(2)
            message_id = self.env['ds_send_email_payslips.message.wizard'].create(
                {'message': _("In the next few minutes, email payslips will be sent to employees.")})

            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'ds_send_email_payslips.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    def action_send_mail(self):
        """ Check if the payslip has been sent via click button send mail and update the status. """
        if self.model == 'hr.payslip':
            payslip = self.env['hr.payslip'].browse(self.res_id)
            payslip.write({'email_send_status': 'sent'})

        res = super(MailComposer, self).action_send_mail()
        return res
