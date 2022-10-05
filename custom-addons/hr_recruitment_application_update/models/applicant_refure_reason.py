# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApplicantGetRefuseReason(models.TransientModel):
    _inherit = "applicant.get.refuse.reason"
    _description = 'Get Refuse Reason'

    send_mail = fields.Boolean("Send Email", compute='_compute_send_mail', store=True, readonly=False)

    @api.depends('refuse_reason_id')
    def _compute_send_mail(self):
        for wizard in self:
            template = wizard.refuse_reason_id.template_id
            wizard.send_mail = False
            wizard.template_id = template

    def action_refuse_reason_apply(self):
        # Restore 
        for item in self:
            item.applicant_ids.check_contract_click = False
            item.applicant_ids.check_pass_interview = False
            item.applicant_ids.check_send_mail_confirm = False
            item.applicant_ids.check_signed_click = False

        if self.send_mail:
            if not self.template_id:
                raise UserError(_("Email template must be selected to send a mail"))
            if not self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email):
                raise UserError(_("Email of the applicant is not set, email won't be sent."))
        self.applicant_ids.write({'refuse_reason_id': self.refuse_reason_id.id, 'active': False})
        if self.send_mail:
            applicants = self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email)
            applicants.message_post_with_template(self.template_id.id, **{
                'auto_delete_message': True,
                'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
                'email_layout_xmlid': 'mail.mail_notification_light'
            })
