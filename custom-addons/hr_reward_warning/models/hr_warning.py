# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrAnnouncementTable(models.Model):
    _name = 'hr.announcement'
    _description = 'HR Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']



    def default_select_mail_all_staff(self):
        email_all_staff = 'allstaff@d-soft.com.vn'
        employee_id_all_staff = self.env['hr.employee'].search([('work_email', '=', email_all_staff)]).ids

        return employee_id_all_staff

    name = fields.Char(string='Code No:', help="Sequence Number of the Announcement")
    announcement_reason = fields.Text(string='Title', states={'draft': [('readonly', False)]}, required=True,
                                      readonly=True, help="Announcement Subject")
    state = fields.Selection([('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
                              ('approved', 'Approved'), ('rejected', 'Refused'), ('expired', 'Expired')],
                             string='Status',  default='draft',
                             track_visibility='always')
    requested_date = fields.Date(string='Requested Date', default=datetime.now().strftime('%Y-%m-%d'),
                                 help="Create Date of Record")
    attachment_id = fields.Many2many('ir.attachment', 'doc_warning_rel', 'doc_id', 'attach_id4',
                                     string="Attachment", help='You can attach the copy of your Letter')
    company_id = fields.Many2one('res.company', string='Company', help="Login user Company")
    is_announcement = fields.Boolean(string='Is general Announcement?', help="To set Announcement as general announcement")
    announcement_type = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'), ('job_position', 'By Job Position')])
    employee_ids = fields.Many2many('hr.employee', 'hr_employee_announcements', 'announcement', 'employee',
                                    string='Employees', help="Employee's which want to see this announcement")
    department_ids = fields.Many2many('hr.department', 'hr_department_announcements', 'announcement', 'department',
                                      string='Departments', help="Department's which want to see this announcement")
    position_ids = fields.Many2many('hr.job', 'hr_job_position_announcements', 'announcement', 'job_position',
                                    string='Job Positions',help="Job Position's which want to see this announcement")
    announcement = fields.Html(string='Letter', states={'draft': [('readonly', False)]}, readonly=True, help="Announcement Content")
    date_start = fields.Date(string='Start Date', default=fields.Date.today(), required=True, help="Start date of "
                                                                                                   "announcement want"
                                                                                                   " to see")
    date_end = fields.Date(string='End Date', default=fields.Date.today(), required=True, help="End date of "
                                                                                               "announcement want too"
                                                                                               " see")

    email_to = fields.Many2many('hr.employee', string="Send To", default=lambda self: self.default_select_mail_all_staff())
    
    def reject(self):
        self.state = 'rejected'

    def approve(self):
        self.state = 'approved'

        subject = self.announcement_reason
        mail_template_id = 'hr_reward_warning.announcements_template_mail'
        self._sendmail_announcements_for_employee({item: item.email_to for item in self}, subject, mail_template_id)


    def sent(self):
        self.state = 'to_approve'

    @api.model
    def _sendmail_announcements_for_employee(self, announcements_item, subject, mail_template_id):
        template_id = self.env['ir.model.data']._xmlid_to_res_id(mail_template_id, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        anno_model_description = self.env['ir.model']._get(self._name).display_name
        for value, users in announcements_item.items():
            if not users:
                continue
            values = {
                'letter': value.announcement,
                'object': value,
                'model_description': anno_model_description,
                'access_link': value._notify_get_action_link('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
                value.message_notify(
                    subject = _(subject),
                    body = assignation_msg,
                    partner_ids = user.user_id.partner_id.ids,
                    record_name = value.announcement_reason,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = anno_model_description,
                )

    @api.constrains('date_start', 'date_end')
    def validation(self):
        if self.date_start > self.date_end:
            raise ValidationError("Start date must be less than End Date")

    @api.model
    def create(self, vals):
        if vals.get('is_announcement'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement.general')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.announcement')
        return super(HrAnnouncementTable, self).create(vals)

    def get_expiry_state(self):
        """
        Function is used for Expiring Announcement based on expiry date
        it activate from the crone job.

        """
        now = datetime.now()
        now_date = now.date()
        ann_obj = self.search([('state', '!=', 'rejected')])
        for recd in ann_obj:
            if recd.date_end < now_date:
                recd.write({
                    'state': 'expired'
                })
