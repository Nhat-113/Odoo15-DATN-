
from datetime import date
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SupportServices(models.Model):
    _name = "support.services"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Request Services"
    _order = "id DESC"

    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    name = fields.Char("Subject", required=True)
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)  
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    date_request = fields.Date(string="Date Request", required=True, default=fields.Date.today)
    description = fields.Text(string="Description", tracking=True)
    requester_id = fields.Many2one('res.users', string='Requester', required=True, tracking=True, default=lambda self: self.env.user)
    project_name = fields.Char('Project Name')
    project_type = fields.Many2one('project.type', string="Project Type", readonly=False, store=True)
    project_pm = fields.Many2one('res.users', string='Project Manager', tracking=True, default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_project = fields.Many2one('res.company', string='Company Project')
    approval = fields.Many2one('res.users', string='Approval', tracking=True, required=False, readonly=False)
    send_to = fields.Many2many('res.users', string='Send To', tracking=True, required=True, readonly=False)
    amount = fields.Monetary(string='Amount', tracking=True, currency_field='currency_vnd')
    status = fields.Many2one('status.support.service', string="Status", default=lambda self: self.env['status.support.service'].search([('type_status', '=', 'draft')]).id)
    domain_status = fields.Char(string="Category domain", readonly=True, store=False, compute='_compute_domain_status')
    flag_status = fields.Char(string="Status Flag", readonly=True, store=True, compute='_compute_flag_status')
    category = fields.Many2one('category.support.service', string="Category", required=True, default=lambda self: self.env['category.support.service'].search([('type_category', '=', 'tam_ung_luong')]).id)
    domain_category = fields.Char(string="Category domain", readonly=True, store=False, compute='_compute_domain_category')
    flag_category = fields.Char(string="Category Flag", readonly=True, store=True, compute='_compute_flag_category')
    active = fields.Boolean(default=True)
    refuse_reason = fields.Char(string='Refuse Reason:', tracking=True)
    payment = fields.Many2one('payment.support.service', string="Payment", required=True, default=lambda self: self.env['payment.support.service'].search([('type_payment', '=', 'no_cost')]).id)
    flag_payment = fields.Char(string="Payment Flag", readonly=True, store=True, compute='_compute_flag_payment')
    check_role_it = fields.Boolean(default=False, compute='compute_check_role_it')

    @api.depends('category')
    def compute_check_role_it(self):
        for request in self:
            if request.payment.type_payment == 'no_cost' and request.env.user.has_group('ds_support_services.support_service_it') == True\
                and request.env.user.has_group('ds_support_services.support_service_pm') == False :
                request.check_role_it = True
            else:
                request.check_role_it = False

    @api.onchange('name')
    def _compute_domain_category(self):
        for record in self:
            if record.env.user.has_group('ds_support_services.support_service_pm') == True:
                record.domain_category = json.dumps([('type_category', '!=', False)])
            else:
                record.domain_category = json.dumps([('type_category', 'in', ['tam_ung_luong', 'it_helpdesk', 'other'])])

    @api.onchange('category', 'payment')
    def _compute_domain_status(self):
        for record in self:
            if record.category.type_category in ['open_projects', 'it_helpdesk', 'other'] and record.payment.type_payment == 'no_cost':
                record.domain_status = json.dumps([('type_status', 'in', ['draft', 'request', 'done'])])
            else:
                record.domain_status = json.dumps([('type_status', '!=', False)])

    @api.depends('category')
    def _compute_flag_category(self):
        for record in self:
            record.flag_category = record.category.type_category

    @api.depends('status')
    def _compute_flag_status(self):
        for record in self:
            record.flag_status= record.status.type_status

    @api.depends('payment')
    def _compute_flag_payment(self):
        for record in self:
            record.flag_payment = record.payment.type_payment
            
    @api.onchange('category', 'company_id', 'payment')
    def get_user_send_to(self):
        for record in self:
            sub_ceo = self.get_user_sub_ceo() 
            HR_user_ids = self.get_user_HR()
            IT_user_ids = self.get_user_IT()
            
            building = []
            it_help = []
            open_prj = []
            for HR_user_id in HR_user_ids:
                    building.append(HR_user_id)
                    it_help.append(HR_user_id)
                    open_prj.append(HR_user_id)
            
            for IT_user_id in IT_user_ids:
                it_help.append(IT_user_id)

            if record.category.type_category in ['team_building', 'tam_ung_luong']:
                record.approval = sub_ceo
                record.send_to = building if len(building) > 0 else False
            elif record.category.type_category == 'it_helpdesk':
                if record.payment.type_payment == 'no_cost':
                    record.send_to = it_help if len(it_help) > 0 else False
                    record.approval = False
                elif record.payment.type_payment == 'have_cost':
                    record.approval = sub_ceo
                    record.send_to = it_help if len(it_help) > 0 else False
            elif record.category.type_category == 'open_projects':
                record.approval = False
                record.send_to = open_prj if len(open_prj) > 0 else False
            else:
                record.send_to = False
                if record.payment.type_payment == 'have_cost':
                    record.approval = sub_ceo
    
    def get_user_sub_ceo(self):
        return self.env['res.users'].search([('login', '=', self.company_id.user_email)]).id
    
    def get_user_HR(self):
        user_HRs = self.env['department.it.hr'].search([('name', '=', 'HR')]).user_ids
        list_id_hrs = []
        for user_hr in user_HRs:
            list_id_hrs.append(user_hr.user_ids.id)
        return list_id_hrs

    def get_user_IT(self):
        mail_ITs = self.env['department.it.hr'].search([('name', '=', 'IT')]).user_ids
        list_id_its = []
        for mail_IT in mail_ITs:
            list_id_its.append(mail_IT.user_ids.id)
        return list_id_its

    def action_request_service(self):
        self.status = self.env['status.support.service'].search([('type_status', '=', 'request')]).id

        # Send mail submit (from pm to director)
        mail_template = "ds_support_services.request_service_template"
        subject_template = "Submit Request Service"

        self._send_message_auto_subscribe_notify_request_service(self.approval , mail_template, subject_template)
    
    def action_approve_service(self):
        self.status = self.env['status.support.service'].search([('type_status', '=', 'approval')]).id

        mail_template_user = "ds_support_services.approvals_request_service_template_user"
        mail_template_send_to = "ds_support_services.approvals_request_service_template_send_to"
        subject_template = "Submit Approve Service"

        self._send_message_auto_subscribe_notify_request_service(self.requester_id, mail_template_user, subject_template)
        self._send_message_auto_subscribe_notify_request_service(self.send_to, mail_template_send_to, subject_template)

    def action_done_service(self):
        self.status = self.env['status.support.service'].search([('type_status', '=', 'done')]).id

        mail_template = "ds_support_services.done_request_service_template"
        subject_template = "Submit Done Service"

        self._send_message_auto_subscribe_notify_request_service(self.requester_id , mail_template, subject_template)

    def action_create_project_service(self):
        self.status = self.env['status.support.service'].search([('type_status', '=', 'done')]).id

        self.env['project.project'].create({
            'name': self.project_name,
            'company_id': self.company_project.id,
            'user_id': self.project_pm.id,
            'project_type': self.project_type.id
        })

        mail_template = "ds_support_services.create_project_request_service_template"
        subject_template = "Submit Done Service"

        self._send_message_auto_subscribe_notify_request_service(self.requester_id , mail_template, subject_template)

    @api.model
    def _send_message_auto_subscribe_notify_request_service(self, users_per_task, mail_template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(mail_template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        for users in users_per_task:
            if not users:
                continue
            values = {
                'object': self,
                'model_description': "Request",
                'access_link': self._notify_get_action_link('view'),
            }
            
            for user in users:
                values['dear'] = user.sudo().name
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                self.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = user.partner_id.ids,
                    record_name = self.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Support Service",
                )

    def action_refuse_reason(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Reason'),
            'res_model': 'hr.request.service.refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_service_ids': self.id},
            'views': [[False, 'form']]
        }

    def toggle_active(self):
        for request in self:
            request.write(
                {'active': True})
    
    def action_set_to_draft(self):
        for request in self:
            request.write({
                'status': self.env['status.support.service'].search([('type_status', '=', 'draft')]).id
            })

    def unlink(self):
        for request in self:
            if request.env.user.has_group('ds_support_services.support_service_admin') == False and request.status.type_status in ['approval', 'done']:
                raise UserError('You cannot delete a request service which is Approval or Done')
        return super().unlink()
    
    @api.constrains('amount')
    def check_amount_validate(self):
        for request in self:
            if request.amount <= 0 and request.category.type_category in ['team_building', 'tam_ung_luong']:
               raise UserError('Amount cannot be less than or equal to 0')

    @api.constrains('date_request')
    def check_date_request_validate(self):
        for request in self:
            if request.date_request > date.today() and request.env.user.has_group('ds_support_services.support_service_hr') == False:
                raise UserError('Date Request cannot be before current date')
        


class DepartmentItHr(models.Model):
    _name = "department.it.hr"

    name = fields.Char(string='Name', store=True)
    user_ids = fields.Many2many('res.users', string='User', readonly=False)