
from datetime import date
import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

LIST_MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]

class SupportServices(models.Model):
    _name = "support.services"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Request Services"
    _order = "id DESC"

    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    def _get_years(self):
        year_list = []
        for i in range(date.today().year - 10, date.today().year + 10):
            year_list.append((str(i), str(i)))
        return year_list

    def _get_year_defaults(self):
        return str(date.today().year)
    
    def _get_month_defaults(self):
        return str(date.today().month)


    name = fields.Char("Subject", required=True)
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)  
    project_id = fields.Many2one('project.project', string="Project", tracking=True)
    date_request = fields.Date(string="Date Request", required=True, tracking=True, default=fields.Date.today)
    description = fields.Text(string="Description", tracking=True)
    requester_id = fields.Many2one('res.users', string='Requester', required=True, tracking=True, default=lambda self: self.env.user)
    project_name = fields.Char('Project Name')
    project_type = fields.Many2one('project.type', string="Project Type", readonly=False, store=True)
    project_pm = fields.Many2one('res.users', string='Project Manager', tracking=True, default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    company_project = fields.Many2one('res.company', string='Company Project')
    approval = fields.Many2one('res.users', string='Approver', tracking=True, required=False, readonly=False)
    send_to = fields.Many2many('res.users', string='Send To', tracking=True, required=True, readonly=False)
    amount = fields.Monetary(string='Amount', tracking=True, currency_field='currency_vnd')
    status = fields.Many2one('status.support.service', tracking=True, string="Status", default=lambda self: self.env['status.support.service'].search([('type_status', '=', 'draft')]).id)
    domain_status = fields.Char(string="Status domain", readonly=True, store=False, compute='_compute_domain_status')
    flag_status = fields.Char(string="Status Flag", readonly=True, store=True, compute='_compute_flag_status')
    category = fields.Many2one('category.support.service',tracking=True, string="Category", required=True, default=lambda self: self.env['category.support.service'].search([('type_category', '=', 'salary_advance')]).id)
    domain_category = fields.Char(string="Category domain", readonly=True, store=False, compute='_compute_domain_category')
    flag_category = fields.Char(string="Category Flag", readonly=True, store=True, compute='_compute_flag_category')
    active = fields.Boolean(default=True)
    refuse_reason = fields.Char(string='Refuse Reason:', tracking=True)
    payment = fields.Many2one('payment.support.service', string="Payment", tracking=True, required=True, default=lambda self: self.env['payment.support.service'].search([('type_payment', '=', 'no_cost')]).id)
    flag_payment = fields.Char(string="Payment Flag", readonly=True, store=True, compute='_compute_flag_payment')
    check_role_it = fields.Boolean(default=False, compute='compute_check_role_it')
    check_role_officer = fields.Boolean(default=False, compute='compute_check_role_officer')
    domain_company_id = fields.Char(string="Company domain", readonly=True, store=False, compute='_compute_domain_company')
    check_invisible_approve = fields.Boolean(default=False, compute='compute_check_invisible_approve')
    check_invisible_field_approver = fields.Boolean(default=False, compute='compute_check_invisible_field_approver')
    payroll_service_id = fields.One2many('payroll.support.service', 'support_service_id')
    check_readonly_field_payroll = fields.Boolean(default=False, compute='compute_check_readonly_field_payroll')
    cost_type = fields.Many2one('cost.support.service', tracking=True, string="Cost Type")
    flag_cost = fields.Char(string="Status Flag", readonly=True, store=True, compute='_compute_flag_cost_type')
    department_id = fields.Many2one('hr.department', string="Department", tracking=True)
    amount_it_other = fields.Monetary(string='Request payment', tracking=True, currency_field='currency_vnd')
    check_invisible_project_id = fields.Boolean(default=False, compute='compute_check_invisible_project_id')
    get_month_tb = fields.Selection(selection=LIST_MONTHS, default=_get_month_defaults, string="Month", required=True, tracking=True)
    get_year_tb = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Year', required=True, tracking=True)
    member_team_building = fields.One2many('booking.team.building', 'support_service_id', string='Member')
    member_ids = fields.Many2many('hr.employee', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    company_ids = fields.Many2many('res.company', string='Companies')
    expense_type = fields.Many2one('expense.support.service', tracking=True, string="Expense Type")
    category_expense = fields.Many2one('expense.general.category', tracking=True, string="Expense Category")
    domain_department_id = fields.Char(string="Department domain", readonly=True, store=False, compute='_compute_domain_project_department')
    domain_project_id = fields.Char(string="Project domain", readonly=True, store=False, compute='_compute_domain_project_department')
    check_readonly_field_project = fields.Boolean(default=False, compute='compute_domain_readonly_project')

    actual_payment = fields.Monetary(string='Actual payment', tracking=True, currency_field='currency_vnd')

    @api.onchange('project_id', 'category', 'get_month_tb')
    def get_member_line(self):
        if self.project_id and self.category.type_category == "team_building":
            member_line = []
            member_ids = []
            month_request = int(self.get_month_tb)
            mem = self.project_id.planning_calendar_resources
            
            for rec in mem:
                if month_request >= rec.start_date.month \
                    and month_request <= rec.end_date.month:
                    member_ids.append(rec.employee_id.id)

            member_line = [(5, 0, 0)]
            for item in member_ids:
                member_line.append((0, 0, {
                    'employee_id': item
                }))
            self.update({"member_team_building": member_line})

    @api.depends('category')
    def compute_check_role_it(self):
        for request in self:
            if request.payment.type_payment == 'no_cost' and request.env.user.has_group('ds_support_services.support_service_it') == True\
                and request.env.user.has_group('ds_support_services.support_service_pm') == False :
                request.check_role_it = True
            else:
                request.check_role_it = False

    @api.depends('category', 'payment', 'status', 'cost_type')
    def compute_domain_readonly_project(self):
        for request in self:
            if request.status.type_status != 'draft' and request.category.type_category != 'team_building' and request.cost_type.type_cost == False or\
                request.category.type_category in ['other', 'it_helpdesk'] and request.status.type_status in ['approval', 'done'] or\
                request.category.type_category == 'team_building' and request.status.type_status != 'draft':
                request.check_readonly_field_project = True
            else:
                request.check_readonly_field_project = False

    @api.onchange('member_team_building')
    def add_booking_team_building(self):
        employee_ids = [employee.id for employee in self.member_team_building.employee_id]
        self.member_ids = self.env['hr.employee'].search([('id', 'in', employee_ids)])

        amount_tb = 0
        for member in self.member_team_building:
            amount_tb += member.amount
        self.amount = amount_tb
    
    @api.depends('category', 'payment', 'status')
    def compute_check_invisible_approve(self):
        for request in self:
            if request.payment.type_payment == 'no_cost' and request.category.type_category in ['it_helpdesk', 'open_projects', 'other']:
                request.check_invisible_approve = True
            else:
                request.check_invisible_approve = False

    @api.depends('category', 'payment', 'status')
    def compute_check_invisible_field_approver(self):
        for request in self:
            if request.category.type_category == 'open_projects' or \
                request.payment.type_payment == 'no_cost' and request.category.type_category in ['it_helpdesk', 'other']:
                request.check_invisible_field_approver = True
            else:
                request.check_invisible_field_approver = False

    @api.depends('category', 'payment', 'status', 'cost_type', 'amount', 'name', 'send_to')
    def compute_check_invisible_project_id(self):
        for request in self:
            if request.category.type_category == 'team_building' or \
                request.category.type_category in ['it_helpdesk', 'other'] and request.cost_type.type_cost == 'cost_project':
                request.check_invisible_project_id = False
            else:
                request.check_invisible_project_id = True
    
    # @api.onchange('project_id', 'category')
    # def set_member_team_building(self):
    #     for request in self:
    #         if request.category.type_category == 'team_building':
    #             request.member_team_building = False

    @api.depends('name', 'approval','category')
    def compute_check_role_officer(self):
        for request in self:
            if request.env.user.has_group('ds_support_services.support_service_sub_ceo') == True:
                request.check_role_officer = True
            else:
                request.check_role_officer = False
                if request.category.type_category in ['team_building', 'salary_advance'] or \
                request.payment.type_payment == 'have_cost' and request.category.type_category in ['it_helpdesk', 'other']:
                    request.approval = request.get_user_sub_ceo()
                else:
                    request.approval = False

    @api.depends('name', 'approval','category')
    def compute_check_readonly_field_payroll(self):
        for request in self:
            if request.env.user.has_group('ds_support_services.support_service_hr') == False:
                request.check_readonly_field_payroll = True
            else:
                request.check_readonly_field_payroll = False

    @api.onchange('name')
    def _compute_domain_category(self):
        for record in self:
            if record.env.user.has_group('ds_support_services.support_service_pm') == True:
                record.domain_category = json.dumps([('type_category', '!=', False)])
            else:
                record.domain_category = json.dumps([('type_category', 'in', ['salary_advance', 'it_helpdesk', 'other'])])

    @api.depends('requester_id')
    def _compute_domain_company(self):
        for record in self:
            record.domain_company_id = json.dumps([('id', 'in', record.requester_id.company_ids.ids)])

    @api.depends('company_id')
    def _compute_domain_project_department(self):
        for record in self:
            record.domain_project_id = json.dumps([('company_id', '=', record.company_id.id)])
            record.domain_department_id = json.dumps([('company_id', '=', record.company_id.id)])

    @api.onchange('category', 'payment')
    def _compute_domain_status(self):
        for record in self:
            if record.category.type_category in ['open_projects', 'it_helpdesk', 'other'] and record.payment.type_payment == 'no_cost':
                record.domain_status = json.dumps([('type_status', 'in', ['draft', 'request', 'done'])])
            elif record.status.type_status != 'refuse':
                if record.category.type_category == 'salary_advance':
                    record.domain_status = json.dumps([('type_status', '!=', 'refuse')])
                else:
                    record.domain_status = json.dumps([('type_status', 'not in', ['refuse', 'repaid'])])
            else:
                if record.category.type_category == 'salary_advance':
                    record.domain_status = json.dumps([('type_status', '!=', False)])
                else:
                    record.domain_status = json.dumps([('type_status', '!=', 'repaid')])

    @api.depends('category')
    def _compute_flag_category(self):
        for record in self:
            record.flag_category = record.category.type_category

    @api.depends('status')
    def _compute_flag_status(self):
        for record in self:
            record.flag_status= record.status.type_status
    
    @api.depends('cost_type')
    def _compute_flag_cost_type(self):
        for record in self:
            record.flag_cost= record.cost_type.type_cost

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

            if record.category.type_category in ['team_building', 'salary_advance']:
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
        mail_template_no_payment = "ds_support_services.request_service_template_no_payment"
        subject_template = "["+self.category.name+"] Submit Request Service"

        if self.category.type_category in ['team_building', 'salary_advance'] or \
            self.payment.type_payment == 'have_cost' and self.category.type_category in ['it_helpdesk', 'other']:
                self._send_message_auto_subscribe_notify_request_service(self.approval , mail_template, subject_template)
        else:
            self._send_message_auto_subscribe_notify_request_service(self.send_to , mail_template_no_payment, subject_template)
    
    def action_approve_service(self):
        if self.cost_type.type_cost == False and self.category.type_category in ['other', 'it_helpdesk'] and self.payment.type_payment == 'have_cost':
           raise UserError('Cost Type cannot be blank.')

        self.status = self.env['status.support.service'].search([('type_status', '=', 'approval')]).id

        mail_template_user = "ds_support_services.approvals_request_service_template_user"
        mail_template_send_to = "ds_support_services.approvals_request_service_template_send_to"
        subject_template = "["+self.category.name+"] Submit Approved Service"

        self._send_message_auto_subscribe_notify_request_service(self.requester_id, mail_template_user, subject_template)
        self._send_message_auto_subscribe_notify_request_service(self.send_to, mail_template_send_to, subject_template)

    def action_done_service(self):
        self.status = self.env['status.support.service'].search([('type_status', '=', 'done')]).id

        mail_template = "ds_support_services.done_request_service_template"
        subject_template = "["+self.category.name+"] Submit Done Service"

        if self.amount_it_other <= 0 and self.category.type_category in ['it_helpdesk', 'other'] and self.payment.type_payment == 'have_cost':
            raise UserError('Amount cannot be less than or equal to 0.')
        
        self.generate_company_expense()

        self._send_message_auto_subscribe_notify_request_service(self.requester_id , mail_template, subject_template)

    def action_repaid_service(self):
        total_advance_payroll = sum([advance.amount for advance in self.payroll_service_id])
        if self.amount != total_advance_payroll:
           raise UserError('Cannot click repaid when the advance payment has not been fully paid')

        self.status = self.env['status.support.service'].search([('type_status', '=', 'repaid')]).id

        mail_template = "ds_support_services.repaid_request_service_template"
        subject_template = "["+self.category.name+"] Submit Repaid Service"

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
        subject_template = "["+self.category.name+"] Submit Done Service"

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
                {'status': self.env['status.support.service'].search([('type_status', '=', 'draft')]).id})

    def unlink(self):
        for request in self:
            if request.env.user.has_group('ds_support_services.support_service_admin') == False and request.status.type_status in ['approval', 'done', 'repaid']:
                raise UserError('You cannot delete a request service which is Approval or Done.')
            request.member_team_building.unlink()
        return super().unlink()
    
    @api.constrains('amount')
    def check_amount_validate(self):
        for request in self:
            if request.amount <= 0 and request.category.type_category in ['team_building', 'salary_advance']:
               raise UserError('Amount cannot be less than or equal to 0.')

    @api.constrains('date_request')
    def check_date_request_validate(self):
        for request in self:
            if request.date_request < date.today() and request.env.user.has_group('ds_support_services.support_service_hr') == False:
                raise UserError('Request date cannot be earlier than today.')
        
    @api.constrains('amount', 'requester_id', 'category')
    def check_amount_advance_salary(self):
        for request in self:
            if request.category.type_category == 'salary_advance' and (request.requester_id.employee_id.id or request.requester_id.employee_ids.id): 
                contract = self.env['hr.contract'].sudo().search([
                    ('employee_id', '=', request.requester_id.employee_id.id or request.requester_id.employee_ids.id),
                    ('date_start', '<=', request.date_request),
                    ('active', '=', True),
                    ('state', 'in', ['draft','open']),
                    '|', ('date_end', '>=', request.date_request),
                    ('date_end', '=', False)
                    ])
                if len(contract)>0 and request.amount > (contract[0].wage + contract[0].taxable_allowance + contract[0].non_taxable_allowance)*2\
                    and request.category.type_category == 'salary_advance':
                   raise UserError('Do not input amount more than 2 months salary')
                elif len(contract)==0 and request.category.type_category == 'salary_advance':
                   raise UserError('No advance without a contract')
    
    def generate_company_expense(self):
        for request in self:
            if request.category.type_category in ['it_helpdesk','other'] and request.payment.type_payment == 'have_cost':
                if request.cost_type.type_cost == 'cost_general':
                    generate_expense = self.env['expense.management'].search([
                            ('company_id', 'in', request.company_ids.ids),
                            ('get_month', '=', str(request.date_request.month)),
                            ('get_year', '=', str(request.date_request.year))
                        ])
                    if len(generate_expense) == 1:
                        expense_management_id = generate_expense
                    elif len(generate_expense) == 0:
                        generate_expense_new = self.env['expense.management'].create({
                            'description': str(request.date_request.month)+'/'+ str(request.date_request.year),
                            'get_month': str(request.date_request.month),
                            'get_year': str(request.date_request.year),
                            'company_id': request.company_ids.ids,
                        })
                        expense_management_id = generate_expense_new


                    if request.expense_type.type_expense == 'activity_expense':
                        self.env['expense.general'].create({
                            'expense_management_id': expense_management_id.id,
                            'category_expenses': request.category_expense.id,
                            'total_expenses': request.actual_payment,
                            'description': request.name
                        })
                    else:
                        self.env['expense.activity'].create({
                            'expense_management_id': expense_management_id.id,
                            'category_expenses': request.category_expense.id,
                            'total_expenses': request.actual_payment,
                            'description': request.name
                        })
                elif request.cost_type.type_cost == 'cost_department':
                    department_expense = self.env['project.expense.management'].search([
                            ('company_id', '=', request.company_id.id),
                            ('department_id', '=', request.department_id.id),
                            ('project_id', '=', False),
                        ])
                    if len(department_expense) == 1:
                        department_expense_management_id = department_expense
                    else:
                        department_expense_new = self.env['project.expense.management'].create({
                            'company_id': request.company_id.id,
                            'department_id': request.department_id.id,
                            'project_id': False
                        })
                        department_expense_management_id = department_expense_new


                    if department_expense_management_id.currency_id.name == 'VND':
                        self.env['project.expense.value'].create({
                            'project_expense_management_id': department_expense_management_id.id,
                            'name': request.name,
                            'expense_date': request.date_request,
                            'total_expenses': request.actual_payment,
                            'expense_vnd': request.actual_payment
                        })
                    else:
                        self.env['project.expense.value'].create({
                            'project_expense_management_id': department_expense_management_id.id,
                            'name': request.name,
                            'expense_date': request.date_request,
                            'total_expenses': 0,
                            'expense_vnd': request.actual_payment
                        })
                else:
                    project_expense = self.env['project.expense.management'].search([
                            ('company_id', '=', request.company_id.id),
                            ('department_id', '=', request.project_id.department_id.id),
                            ('project_id', '=', request.project_id.id),
                        ])
                    if len(project_expense) == 1:
                        project_expense_management_id = project_expense
                    elif len(project_expense) == 0:
                        project_expense_new = self.env['project.expense.management'].create({
                            'company_id': request.company_id.id,
                            'department_id': request.project_id.department_id.id,
                            'project_id': request.project_id.id
                        })
                        project_expense_management_id = project_expense_new

                    
                    if project_expense_management_id.currency_id.name == 'VND':
                        self.env['project.expense.value'].create({
                            'project_expense_management_id': project_expense_management_id.id,
                            'name': request.name,
                            'expense_date': request.date_request,
                            'total_expenses': request.actual_payment,
                            'expense_vnd': request.actual_payment,
                            'description': request.description
                        })
                    else:
                        self.env['project.expense.value'].create({
                            'project_expense_management_id': project_expense_management_id.id,
                            'name': request.name,
                            'expense_date': request.date_request,
                            'total_expenses': 0,
                            'expense_vnd': request.actual_payment,
                            'description': request.description
                        })
            elif request.category.type_category == 'team_building':
                project_expense = self.env['project.expense.management'].search([
                            ('company_id', '=', request.company_id.id),
                            ('department_id', '=', request.project_id.department_id.id),
                            ('project_id', '=', request.project_id.id),
                        ])
                if len(project_expense) == 1:
                    project_expense_management_id = project_expense
                elif len(project_expense) == 0:
                    project_expense_new = self.env['project.expense.management'].create({
                        'company_id': request.company_id.id,
                        'department_id': request.project_id.department_id.id,
                        'project_id': request.project_id.id
                    })
                    project_expense_management_id = project_expense_new

                
                if project_expense_management_id.currency_id.name == 'VND':
                    self.env['project.expense.value'].create({
                        'project_expense_management_id': project_expense_management_id.id,
                        'name': request.name,
                        'expense_date': request.date_request,
                        'total_expenses': request.amount,
                        'expense_vnd': request.amount
                    })
                else:
                    self.env['project.expense.value'].create({
                        'project_expense_management_id': project_expense_management_id.id,
                        'name': request.name,
                        'expense_date': request.date_request,
                        'total_expenses': 0,
                        'expense_vnd': request.amount
                    })

    @api.constrains('name', 'project_id', 'member_team_building')
    def check_booking_team_building(self):
        for request in self:
            if len(request.member_team_building) == 0 and request.category.type_category == 'team_building':
               raise UserError('You have not booked any members for request team building')

class DepartmentItHr(models.Model):
    _name = "department.it.hr"

    name = fields.Char(string='Name', store=True)
    user_ids = fields.Many2many('res.users', string='User', readonly=False)