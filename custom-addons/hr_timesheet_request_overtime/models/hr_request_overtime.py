import datetime
import hashlib
import hmac
import json
from werkzeug import urls
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import pandas as pd


class HrRequestOvertimeStage(models.Model):
    _name = "hr.request.overtime.stage"
    _description = "Timesheet Request Overtime Stages"
    _order = 'sequence'

    name = fields.Char("Stage Name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")
    confirm_stage = fields.Boolean('Confirm Stage',
        help="...")
    
    @api.model
    def create(self, vals_list):
        return super().create(vals_list)
    

class HrRequestOverTime(models.Model):
    _name = "hr.request.overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Hr Request Overtime"
    _order = "id DESC"

    def _get_default_stage_id(self):
        return self.env['hr.request.overtime.stage'].search([], limit=1).id

    def _get_default_approve(self):
        representative = self.env['res.users'].search([('email','=',self.env.company.user_email)])
        return representative.id

    name = fields.Char("Subject", required=True, tracking=True)

    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True, store=True)
    get_domain_projects = fields.Char(string='Domain Project', readonly=True, store=False, compute='_get_domain_project')
    start_date_project = fields.Date(string="Start date", related='project_id.date_start', store=True)
    end_date_project = fields.Date(string="End date", related='project_id.date', store=True)
    user_id = fields.Many2one(string='Project Manager', related='project_id.user_id', readonly=True)
    
    start_date = fields.Date(string="Start Date", required=True, tracking=True, store=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True, store=True)
    duration_overtime = fields.Integer(compute='_compute_duration_overtime', string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=0)

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    description = fields.Text(string="Description", tracking=True)
    stage_id = fields.Many2one('hr.request.overtime.stage', 'Status', ondelete='restrict',
                            default=_get_default_stage_id, 
                            store=True, readonly=False,
                            group_expand='_read_group_stage_ids',
                            required=True, tracking=True,
                            # domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            )
    domain_stage = fields.Char(string='Domain view stage', compute="_compute_domain_stage")

    request_creator_id = fields.Many2many('res.users', 'hr_request_overtime_res_users_inform_rel', string='Inform to', default=False, tracking=True, store=True)
    requester_id = fields.Many2one('res.users', string='Approver', required=True, default=lambda self: self._get_default_approve(), readonly=False, tracking=True, store=True)
    member_ids = fields.Many2many('hr.employee', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    
    member_ids_user = fields.Many2many('res.users', 'hr_request_overtime_member_ids_users_rel', compute='_compute_member_ids_user', store=True, tracking=True)
    booking_overtime = fields.One2many('hr.booking.overtime', 'request_overtime_id', string='Booking Overtime', store=True, tracking=True)
    timesheet_overtime_id = fields.One2many('account.analytic.line', 'request_overtime_ids')
    active = fields.Boolean(string='Invisible Refuse Button', default=True, store=True)
    refuse_reason_id = fields.One2many('hr.request.overtime.refuse.reason', 'request_overtime_ids', tracking=True)
    refuse_reason = fields.Char('Refuse Reason', tracking=True)

    
    submit_flag = fields.Boolean(default=True)
    confirm_flag = fields.Boolean(default=True)
    approve_flag = fields.Boolean(default=True)
    request_flag = fields.Boolean(default=False)
    read_only_project = fields.Boolean(default=False)

    stage_name = fields.Text(string="Name", compute = '_get_stage_name', default ="Draft", store=True)
    last_stage = fields.Integer(string="Last stage", default=0)

    @api.onchange('stage_id')
    def _compute_domain_stage(self):
        for record in self:
            if record.stage_id.name == 'Refuse':
                record.domain_stage = json.dumps([('name', 'in', ['Draft','Request','Confirm','Submit', 'Approved', 'Refuse'])])
            else:
                record.domain_stage = json.dumps([('name', 'in', ['Draft','Request','Confirm','Submit', 'Approved'])])

    def _compute_invisible_button_refuse(self):
        for record in self:
            if (record.active==True and record.stage_name != 'Approved') or (record.active==True and record.stage_name == 'Approved' and record.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_director') == True):
                record.invisible_button_refuse = False
            else:
                record.invisible_button_refuse = True
                
    invisible_button_refuse = fields.Boolean(default=False, help="Check invisible button Approved", compute="_compute_invisible_button_refuse", store=False)

    @api.depends('member_ids')
    def _compute_member_ids_user(self):
        for record in self:
            record.member_ids_user = record.member_ids.user_id.ids

    
    @api.depends('company_id')
    def _get_domain_project(self):
        for record in self:
            if self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_director') == True and \
                self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_projmanager') == True:
                    project = self.env['project.project'].search([('company_id', '=', record.company_id.id)])
            else:
                project = self.env['project.project'].search([('company_id', '=', record.company_id.id), '|', ('user_id', '=',self.env.user.id), ('member_ids','=',self.env.user.employee_id.id)])
            
            if project:
                project_ids = [item.id for item in project]
            else:
                project_ids = []
            
            record.get_domain_projects = json.dumps([('company_id', '=', record.company_id.id), ('id', 'in', project_ids)])

    def action_refuse_reason(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Reason'),
            'res_model': 'hr.request.overtime.refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_overtime_ids': self.id},
            'views': [[False, 'form']]
        }
       
    def reset_request_overtime(self):
        """ Reinsert the request into the recruitment pipe in the first stage"""
        default_stage = self.env['hr.request.overtime.stage'].search([], order='sequence asc', limit=1).id
        for request in self:
            request.write(
                {'stage_id': default_stage})

    def toggle_active(self):
        res = super(HrRequestOverTime, self).toggle_active()
        request_active = self.filtered(lambda request: request.active)
        if request_active:
            request_active.reset_request_overtime()
        
        request_overtime_inactive = self.filtered(lambda request: not request.active)
        if request_overtime_inactive:
            return request_overtime_inactive.action_refuse_reason()
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Always display all stages """
        return stages.search([], order=order)

    @api.onchange('booking_overtime', 'booking_overtime.date_start', 'booking_overtime.end_date')
    def _add_booking_overtime(self):
        # update member_ids list
        user_ids = [user.id for user in self.booking_overtime.user_id]
        self.member_ids = self.env['hr.employee'].search([('id', 'in', user_ids)])

    @api.onchange('booking_overtime','start_date', 'end_date')
    def _check_duplicate_booking_member(self):
        check_values = {}
        self.common_check_dupplicate(check_values)
        if len(self.booking_overtime)>0 and check_values['booking'] == True:
            warning = {
                        'warning': {
                            'title': 'Warning!',
                            'message': 'The user is booked OT on this date, please recheck.'
                            }
                        }
            return warning
    
    def common_check_dupplicate(self, check_values):
        for record in self:
            if len(record.booking_overtime)>0:
                # new_booking_member = record.booking_overtime[-1]
                current_booking = record.booking_overtime
                check_values['booking'] = False
                for index, booking in enumerate(current_booking):
                    for old_booking in current_booking[index+1:]:
                    # Validation
                        if (old_booking.user_id.id==booking.user_id.id) and \
                            ((old_booking.start_date <= booking.start_date and old_booking.end_date >= booking.start_date) or\
                                (old_booking.start_date <= booking.end_date and old_booking.end_date >= booking.end_date) or\
                                    (old_booking.start_date >= booking.start_date and old_booking.end_date <= booking.end_date)):
                            check_values['booking'] = True

    
    def write(self, vals):
        res = super().write(vals)
        check_values = {}
        self.common_check_dupplicate(check_values)
        if len(self.booking_overtime)>0 and check_values['booking'] == True:
            raise ValidationError(_("The user is booked OT on this date, please recheck."))
        return res
    
    @api.depends('start_date', 'end_date')
    def _compute_duration_overtime(self):
        """ Calculates duration working time"""
        for record in self:
            if record.end_date and record.start_date:
                working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                record.end_date.strftime('%Y-%m-%d')))
                record.duration_overtime = working_days if working_days > 0 else 1
            else:
                record.duration_overtime = 1

    @api.onchange('start_date', 'end_date')
    def _validate_plan_overtime(self):
        if self.end_date and self.start_date:
            # Raise if project missing plan
            if not self.project_id.date_start or not self.project_id.date:
                raise ValidationError(_("Please update plan (start date and end date) for Project."))

            if self.start_date > self.end_date:
                raise ValidationError(_("The Start Date must be smaller than the End Date"))

            # Validation Plan Date Overtime must be within the duration of the project
            if (self.start_date < self.project_id.date_start or self.end_date > self.project_id.date):
                    raise ValidationError(_("Plan Date Overtime must be within the duration of the project."))

    @api.constrains('start_date', 'end_date')
    def _validate_plan_overtime(self):
        for record in self:
            # Validation Plan Date Overtime not overlap in the same project
            project_request_overtime = self.env['hr.request.overtime'].search([('project_id', '=' ,record.project_id.id),('id','!=' ,record.id)])
            for item in project_request_overtime:
                if item.end_date < record.start_date or item.start_date > record.end_date:
                    continue
                else:
                    raise ValidationError(_("Plan Date Overtime can not overlap in the same project. \nRequest Overtime Duplicate Plan is: {}".format(item.name)))

            for booking in record.booking_overtime:
                if not (booking.start_date >= record.start_date and booking.end_date <= record.end_date):
                    raise ValidationError(_("Booking Plan Date Overtime for Member must be within the duration of the Request Overtime.")) 


    def action_submit_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Submit')]).id
        self.submit_flag = False

        # Send mail submit (from pm to director)
        mail_template = "hr_timesheet_request_overtime.submit_request_overtime_template"
        subject_template = "Submit Request Overtime"

        self._send_message_auto_subscribe_notify_request_overtime({self: item.requester_id for item in self}, mail_template, subject_template)
        for record in self.timesheet_overtime_id:
            if record.status_timesheet_overtime != 'approved':
                record.check_request_ot = True
                record.status_timesheet_overtime = 'confirm'
                record.check_request_ot = True

    def action_confirm_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Confirm')]).id
        self.confirm_flag = False

        # Send mail confirm (from director to pm)
        mail_template = "hr_timesheet_request_overtime.confirm_request_overtime_template"
        subject_template = "Confirm Request Overtime"
        # Send mail for Inform-to
        self._send_message_auto_subscribe_notify_request_overtime({self: item.request_creator_id for item in self}, mail_template, subject_template)
        # Send mail for PM
        self._send_message_auto_subscribe_notify_request_overtime({self: item.user_id for item in self}, mail_template, subject_template)

    def action_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Request')]).id
        self.approve_flag = False

        # Send mail request timesheets ot (from pm to director)
        mail_template = "hr_timesheet_request_overtime.request_timesheets_overtime_template"
        subject_template = "Request Timesheets Overtime"
        self._send_message_auto_subscribe_notify_request_overtime({self: item.requester_id for item in self}, mail_template, subject_template)

    def action_approve_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Approved')]).id
        self.approve_flag = False

        # Send mail approvals request overtime (from director to pm)
        mail_template = "hr_timesheet_request_overtime.approvals_request_overtime_template"
        subject_template = "Approvals Request Timesheets Overtime"
        # Send mail for Inform-to
        self._send_message_auto_subscribe_notify_request_overtime({self: item.request_creator_id for item in self}, mail_template, subject_template)
        # Send mail for PM
        self._send_message_auto_subscribe_notify_request_overtime({self: item.user_id for item in self}, mail_template, subject_template)
        # Payment for time off
        for record in self.timesheet_overtime_id:
            if record.status_timesheet_overtime != 'approved':
                record._compute_pay_type_of_timeoff()
                record.status_timesheet_overtime = 'approved'
                record.check_approval_ot = True

    # TODO Fix this, refator code
    @api.depends('stage_id')
    def _get_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name
            if record.stage_id.name == "Draft":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Request":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': False,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Confirm":
                vals = {
                'confirm_flag': False,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Submit":
                vals = {
                'confirm_flag': True,
                'submit_flag': False,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Approved":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': False,
                }
                self.write(vals)

    @api.model
    def _send_message_auto_subscribe_notify_request_overtime(self, users_per_task, mail_template, subject_template):

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

    @api.model
    def _notify_encode_link_request(self, base_link, params):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret')
        token = '%s?%s' % (base_link, ' '.join('%s=%s' % (key, params[key]) for key in sorted(params)))
        hm = hmac.new(secret.encode('utf-8'), token.encode('utf-8'), hashlib.sha1).hexdigest()
        return hm

    def _notify_get_action_link_request(self, link_type, **kwargs):
        """ Prepare link to an action: view document, follow document, ... """
        params = {
            'model': kwargs.get('model', self._name),
            'res_id': kwargs.get('res_id', self.ids and self.ids[0] or False),
        }
        # whitelist accepted parameters: action (deprecated), token (assign), access_token
        # (view), auth_signup_token and auth_login (for auth_signup support)
        params.update(dict(
            (key, value)
            for key, value in kwargs.items()
            if key in ('action', 'token', 'access_token', 'auth_signup_token', 'auth_login')
        ))

        if link_type in ['view', 'assign', 'follow', 'unfollow']:
            base_link = '/mail/%s' % link_type
        elif link_type == 'controller':
            controller = kwargs.get('controller')
            params.pop('model')
            base_link = '%s' % controller
        else:
            return ''

        if link_type not in ['view']:
            token = self._notify_encode_link_request(base_link, params)
            params['token'] = token

        link = '%s?%s' % (base_link, urls.url_encode(params))
        if self:
            link = self.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')]).value + link

        return link
    
    @api.model
    def create(self, vals_list):
        if 'request_flag' in vals_list:
            vals_list['request_flag']=True
            
        vals_list.update({'read_only_project': True})

        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.stage_id.name == "Approved" and record.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_admin') == False:
                raise UserError(_("Can not delete Request Approved!")) 
            record.booking_overtime.unlink()
        return super().unlink()

    