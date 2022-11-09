from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json


class ProjectExpense(models.Model):
    _name = "project.expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Expense Management"
    _rec_name = "name_alias"
    _order = "project_id DESC"
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    name_alias = fields.Char(string="Name Alias", compute='_compute_name_alias', store=True)
    
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project",  tracking=True)
    department_id = fields.Many2one("hr.department", string="Department", required=True, store=True, readonly=False, domain="[('company_id', '=', company_id)]")
    user_pm = fields.Many2one('res.users', string="Div manager", related='department_id.manager_id.user_id', store=True)
    user_subceo = fields.Char(string='Sub CEO email', store=True, related='company_id.user_email')
    start_date = fields.Date(string="Start date", related='project_id.date_start', store=True)
    end_date = fields.Date(string="End date", related='project_id.date', store=True)
    total_expenses = fields.Monetary(string="Total Expense", currency_field='currency_id', compute='_compute_total_expense', store=True)
    description = fields.Text(string="Description", tracking=True)
    
    # rounding_usd_input = fields.Float(string="USD to VND", tracking=True)
    # rounding_jpy_input = fields.Float(string="JPY to VND", tracking=True)
    # rounding_sgd_input = fields.Float(string="SGD to VND", tracking=True)
    
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    # currency_usd = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self._get_default_currency('USD'), readonly=True)    
    # currency_jpy = fields.Many2one('res.currency', string="YPY Currency", default=lambda self: self._get_default_currency('JPY'), readonly=True)   
    # currency_sgd = fields.Many2one('res.currency', string="SGD Currency", default=lambda self: self._get_default_currency('SGD'), readonly=True)   
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)
    
    # expense_usd = fields.Monetary(string="Total Expense", currency_field='currency_usd', store=True, compute="_convert_currency_revenue")
    # expense_jpy = fields.Monetary(string="Total Expense", currency_field='currency_jpy', store=True, readonly=True)
    # expense_sgd = fields.Monetary(string="Total Expense", currency_field='currency_sgd', store=True, readonly=True)
    expense_vnd = fields.Monetary(string="Total Expense", currency_field='currency_vnd', store=True, readonly=True)
    
    get_currency_name = fields.Char(string='Currency Name', readonly=True, related='currency_id.name', store=True)
    get_domain_projects = fields.Char(string='Domain Project', readonly=True, store=False, compute='_get_domain_project')
    
    project_expense_value_ids = fields.One2many('project.expense.value', 'project_expense_management_id', string="Project Expense Value")
    
    
    
    # Remove option in filters, group by from dropdown Search action in formview
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        field_disable = ['user_pm', 'name_alias', 'user_subceo', 'currency_vnd', 'currency_id', 'get_currency_name']
        result = super(ProjectExpense, self).fields_get(allfields, attributes=attributes)
        
        for field in field_disable:
            if field in result:
                result[field].update({
                    'selectable': False,
                    'exportable': False,
                    'searchable': False,
                    'sortable': False
                })
          
        return result
    
    
    @api.depends('department_id', 'project_id')
    def _compute_name_alias(self):
        for record in self:
            if record.project_id:
                record.name_alias = record.project_id.name
            else:
                record.name_alias = record.department_id.name
                
                
    @api.onchange('department_id')
    def _validate_project_department(self):
        if self.department_id:
            if self.project_id:
                if self.project_id.department_id.id not in [self.department_id.id, False]:
                    self.project_id = False
                    self.project_expense_value_ids = False
                
            else:
                expense_db = self.env['project.expense.value'].search([('project_expense_management_id', '=', self.id or self.id.origin), 
                                                                       ('department_id', '=', self.department_id.id),
                                                                       ('project_id', 'in', [False])])
                self.project_expense_value_ids = expense_db
                
    
    
    @api.depends('company_id', 'department_id')
    def _get_domain_project(self):
        for record in self:
            project_expenses = self.search([('company_id', '=', record.company_id.id), ('id', '!=', record.id or record.id.origin)])
            project_ids = project_expenses.project_id.ids
            record.get_domain_projects = json.dumps([('company_id', '=', record.company_id.id), 
                                                ('department_id', 'in', [False, record.department_id.id]),
                                                ('id', 'not in', project_ids if len(project_ids) > 0 else [False])])
              
        
    @api.onchange('company_id')
    def _compute_project_company(self):
        if self.company_id and self.department_id:
            if self.department_id.company_id.id not in [self.company_id.id, False]:
                self.department_id = False
                self.project_id = False
                self.project_expense_value_ids = False
              
            
    @api.depends('project_expense_value_ids.total_expenses', 'project_expense_value_ids.expense_vnd')
    def _compute_total_expense(self):
        for record in self:
            total_revenue_curr = 0
            total_revenue_vnd = 0
            for item in record.project_expense_value_ids:
                total_revenue_curr += item.total_expenses
                total_revenue_vnd += item.expense_vnd
            record.total_expenses = total_revenue_curr
            record.expense_vnd = total_revenue_vnd
            
    
    @api.onchange('project_id')
    def _validate_unique_project_cost(self):
        # project_costs = self.search_count([('id', '!=', self.id or self.id.origin), ('project_id', '=', self.project_id.id)])
        # if project_costs != 0:
        #    raise UserError(_('The project cost "%(project)s" already exists!', project = self.project_id.name))
        # else:
        if self.project_id:
            get_datas = self.env['project.expense.value'].search([('project_expense_management_id', 'in', [self.id or self.id.origin, False]),
                                                                ('project_id', '=', self.project_id.id)])
            
            self.project_expense_value_ids = get_datas
            for record in self.project_expense_value_ids:
                if record.expense_date > self.project_id.date or record.expense_date < self.project_id.date_start:
                    record.write({'project_expense_management_id': [(2, self.id or self.id.origin)]})
        
        else:
            department_expense_db = self.env['project.expense.value'].search([('project_expense_management_id', 'in', [self.id or self.id.origin, False]),
                                                                ('department_id', '=', self.department_id.id)])
            self.project_expense_value_ids = department_expense_db
                    
                    
    @api.constrains('department_id')
    def validate_department_unique(self):
        for record in self:
            department_expenses = self.search([('company_id', '=', record.company_id.id), 
                                              ('project_id', 'in', [False]), 
                                              ('department_id', '=', record.department_id.id),
                                              ('id', '!=', record.id or record.id.origin)])
            if department_expenses and not record.project_id:
                raise ValidationError(_('Department expenses "%s" already exists!', record.department_id.name))
                    
                    
    def unlink(self):
        for record in self:
            record.project_expense_value_ids.unlink()
        return super(ProjectExpense, self).unlink()
    
class ProjectExpenseValue(models.Model):
    _name = 'project.expense.value'
    _rec_name = "name"
    _order = "expense_date DESC"
    
    
    project_expense_management_id = fields.Many2one('project.expense.management', string="Project Expense Management")
    project_id = fields.Many2one('project.project', string="Project", related='project_expense_management_id.project_id', store=True)
    department_id = fields.Many2one("hr.department", string="Department", store=True, related='project_expense_management_id.department_id')
    currency_id = fields.Many2one('res.currency', string="Currency", related='project_expense_management_id.currency_id', store=True)
    
    name = fields.Char(string="Expense name", required=True)
    expense_date = fields.Date(string="Expense Date", required=True)
    total_expenses = fields.Monetary(string="Total Expense", currency_field='currency_id', required=True)
    description = fields.Text(string="Description")
    
    exchange_rate = fields.Float(string="Exchange Rate")
    expense_vnd = fields.Monetary(string="Total Revenue (VND)", currency_field='currency_vnd', compute='_compute_total_expense', store=True)
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", related='project_expense_management_id.currency_vnd', readonly=True)   
    
    
    @api.onchange('expense_date')
    def _validate_duration_expense_date(self):
        self.validate_project_expense_content(action = True)


    @api.onchange('project_id')
    def _validate_duration_project_expense(self):
        self.validate_project_expense_content(action = False)
        
    @api.depends('exchange_rate', 'total_expenses', 'project_expense_management_id.currency_id')
    def _compute_total_expense(self):
        for record in self:
            # if record.project_expense_management_id.currency_id:
            #     record.currency_id = record.project_expense_management_id.currency_id
            if record.currency_id.name == 'VND':
                record.expense_vnd = record.total_expenses
            else:
                record.expense_vnd = record.total_expenses * record.exchange_rate


    def validate_project_expense_content(self, action):
        if self.project_id.id != False and self.expense_date != False:
            if self.project_id.date == False or self.project_id.date_start == False:
                raise UserError(_('The duration of the project is false! Please update duration of project "%(project)s"', 
                                project = self.project_id.name))
            else:
                if self.expense_date > self.project_id.date or self.expense_date < self.project_id.date_start:
                    if action == False:
                        self.expense_date = False
                    else:
                        raise UserError(_('The date "%(date)s" is outside the project implementation period "%(project)s" !',
                                        date = self.expense_date, project = self.project_id.name))