
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class OvertimeGetRefuseReason(models.TransientModel):
    _name = 'hr.request.overtime.refuse.reason'
    _description = 'Get Refuse Reason'


    request_overtime_ids = fields.Many2many('hr.request.overtime')
    subject_refuse_reason = fields.Char(string="Refuse Reason")

    def action_refuse_reason_apply(self):
        print('===========================================')
        # if self.send_mail:
        #     if not self.template_id:
        #         raise UserError(_("Email template must be selected to send a mail"))
        #     if not self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email):
        #         raise UserError(_("Email of the applicant is not set, email won't be sent."))
        # self.applicant_ids.write({'refuse_reason_id': self.refuse_reason_id.id, 'active': False})
        # if self.send_mail:
        #     applicants = self.applicant_ids.filtered(lambda x: x.email_from or x.partner_id.email)
        #     applicants.message_post_with_template(self.template_id.id, **{
        #         'auto_delete_message': True,
        #         'subtype_id': self.env['ir.model.data']._xmlid_to_res_id('mail.mt_note'),
        #         'email_layout_xmlid': 'mail.mail_notification_light'
        #     })