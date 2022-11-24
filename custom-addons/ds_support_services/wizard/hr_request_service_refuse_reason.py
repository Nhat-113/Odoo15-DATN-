
from odoo import api, fields, models, _

class ServiceGetRefuseReason(models.TransientModel):
    _name = 'hr.request.service.refuse.reason'
    _description = 'Get Refuse Reason'

    request_service_ids = fields.Many2one('support.services')
    subject_refuse_reason = fields.Char(string="Refuse Reason", required=True)

    def action_refuse_reason_apply(self):
        subject_template = "Reject Request Service: %s" % self.request_service_ids.display_name
        mail_template = "ds_support_services.refuse_request_service_template"
        self._send_message_auto_subscribe_notify_refuse_request_service({item: item.requester_id for item in self.request_service_ids}, mail_template, subject_template)
        self.request_service_ids.write({
                                    'active': False, 
                                    'refuse_reason': str(self.subject_refuse_reason),
                                    'status': self.env['status.support.service'].search([('type_status', '=', 'draft')]).id
                                    })

    @api.model
    def _send_message_auto_subscribe_notify_refuse_request_service(self, users_per_task, mail_template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(mail_template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        for task, users in users_per_task.items():
            if not users:
                continue

            values = {
                'object': task,
                'model_description': "Request",
                'refuse_reason': self.subject_refuse_reason,
                'access_link': task._notify_get_action_link('view'),
            }
            for user in users:
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = user.partner_id.ids,
                    record_name = task.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Request Service",
                )