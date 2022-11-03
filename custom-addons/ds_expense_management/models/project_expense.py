from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json


class ProjectExpense(models.Model):
    _name = "project.expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Expense Management"
    _rec_name = "project_id"
    _order = "project_id DESC"
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True)
    department_id = fields.Many2one("hr.department", string="Department", related='project_id.department_id', store=True)
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
    
    
    
    @api.depends('company_id')
    def _get_domain_project(self):
        for record in self:
            project_expenses = self.search([('company_id', '=', record.company_id.id), ('id', '!=', record.id or record.id.origin)])
            if project_expenses:
                project_ids = [item.project_id.id for item in project_expenses]
            else:
                project_ids = []
            record.get_domain_projects = json.dumps([('company_id', '=', record.company_id.id), 
                                                    ('id', 'not in', project_ids if len(project_ids) > 0 else [False])])
              
        
    @api.onchange('company_id')
    def _compute_project_company(self):
        if self.project_id.company_id.id != self.company_id.id:
            self.project_id = False
            self.project_expense_value_ids = False
              
    
    # @api.depends('total_expenses', 'rounding_usd_input', 'rounding_jpy_input', 'rounding_sgd_input', 'currency_id')
    # def _convert_currency_revenue(self):
    #     for record in self:
    #         # record.get_currency_name = record.currency_id.name
    #         if record.total_expenses != 0.0:
    #             if record.currency_id.name == 'VND':
    #                 record.expense_vnd = record.total_expenses
    #                 if record.rounding_usd_input != 0.0:
    #                     record.expense_usd = record.total_expenses / record.rounding_usd_input
    #                 else:
    #                     record.expense_usd = 0
    #                 if record.rounding_jpy_input != 0.0:
    #                     record.expense_jpy = record.total_expenses / record.rounding_jpy_input
    #                 else:
    #                     record.expense_jpy = 0
    #                 if record.rounding_sgd_input != 0.0:
    #                     record.expense_sgd = record.total_expenses / record.rounding_sgd_input
    #                 else:
    #                     record.expense_sgd = 0 
                        
    #             elif record.currency_id.name == 'JPY':   
    #                 record.expense_jpy = record.total_expenses
    #                 record.expense_vnd = record.total_expenses * record.rounding_jpy_input
    #                 # if record.rounding_usd_input != 0:
    #                 #     record.expense_usd = record.expense_vnd / record.rounding_usd_input
    #                 # else:
    #                 #     record.expense_usd = 0
                    
    #             elif record.currency_id.name == 'SGD':
    #                 record.expense_sgd = record.total_expenses
    #                 record.expense_vnd = record.total_expenses * record.rounding_sgd_input
                    
    #             else:
    #                 record.expense_usd = record.total_expenses
    #                 record.expense_vnd = record.total_expenses * record.rounding_usd_input
    #                 # record.expense_jpy = record.expense_vnd * record.rounding_jpy_input
    #         else:
    #             record.expense_usd = 0
    #             record.expense_jpy = 0
    #             record.expense_sgd = 0
    #             record.expense_vnd = 0
    
            
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
        get_datas = self.env['project.expense.value'].search([('project_expense_management_id', 'in', [self.id or self.id.origin, False]),
                                                            ('project_id', '=', self.project_id.id)])
        
        self.project_expense_value_ids = get_datas
        for record in self.project_expense_value_ids:
            if record.expense_date > self.project_id.date or record.expense_date < self.project_id.date_start:
                record.write({'project_expense_management_id': [(2, self.id or self.id.origin)]})
                    
                    
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