
from odoo import api, fields, models, _

class OvertimeGetRefuseReason(models.TransientModel):
    _name = 'hr.request.overtime.refuse.reason'
    _description = 'Get Refuse Reason'

    request_overtime_ids = fields.Many2one('hr.request.overtime')
    subject_refuse_reason = fields.Char(string="Refuse Reason", required=True)
    request_without_email = fields.Text(compute='_compute_request_overtime_without_email', string='Applicant(s) not having email')

    def action_refuse_reason_apply(self):
        subject_template = "Reject Request Overtime: %s" % self.request_overtime_ids.display_name
        mail_template = "hr_timesheet_request_overtime.refuse_request_overtime_template"
        self._send_message_auto_subscribe_notify_refuse_request_overtime({item: item.request_creator_id for item in self.request_overtime_ids}, mail_template, subject_template)
        self.request_overtime_ids.write({'active': False, "refuse_reason": str(self.subject_refuse_reason)})

        self.request_overtime_ids.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Draft')]).id
        self.request_overtime_ids.submit_flag = False
        self.request_overtime_ids.confirm_flag = True
        self.request_overtime_ids.request_flag = True
        self.request_overtime_ids.approve_flag = True

    @api.model
    def _send_message_auto_subscribe_notify_refuse_request_overtime(self, users_per_task, mail_template, subject_template):

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
                'access_link': task._notify_get_action_link_request('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                values.update({'dear_name': user.display_name})
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = user.partner_id.ids,
                    record_name = task.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Request Overtime",
                )
