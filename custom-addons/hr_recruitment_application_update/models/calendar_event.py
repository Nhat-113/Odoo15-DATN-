from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
from datetime import timedelta 

class Meeting(models.Model):
    _inherit = 'calendar.event'
    _description = "Calendar Event"

    time_start = fields.Datetime(string="Time interview with mail template", compute="_compute_time_start")

    @api.depends('start')
    def _compute_time_start(self):
        for record in self:
            record.time_start = record.start + timedelta(hours = 7)

    def action_open_composer(self):
        if not self.partner_ids:
            raise UserError(_("There are no attendees on these events"))
        if self.applicant_id:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('hr_recruitment_application_update.email_interview_for_candidate_template', raise_if_not_found=False)
        else:
            template_id = self.env['ir.model.data']._xmlid_to_res_id('calendar.calendar_template_meeting_update', raise_if_not_found=False)
        # The mail is sent with datetime corresponding to the sending user TZ
        composition_mode = self.env.context.get('composition_mode', 'comment')
        compose_ctx = dict(
            default_composition_mode=composition_mode,
            default_model='calendar.event',
            default_res_ids=self.ids,
            default_use_template=bool(template_id),
            default_template_id=template_id,
            default_partner_ids=self.partner_ids.ids,
            mail_tz=self.env.user.tz,
        )
        values = {'name':self.applicant_id.partner_name, 'email':self.applicant_id.email_from}
        result = self.env['res.partner'].create(values)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contact Attendees'),
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': compose_ctx,
        }