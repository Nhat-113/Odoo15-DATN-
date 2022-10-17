from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectExpense(models.Model):
    _name = "project.expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Expense Management"
    _rec_name = "name"
    _order = "expense_date DESC"
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])
    
    name = fields.Char(string="Expense name", required=True, tracking=True)
    expense_date = fields.Date(string="Expense Date", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    total_expenses = fields.Monetary(string="Total Expense", currency_field='currency_id', required=True)
    description = fields.Text(string="Description", tracking=True)
    
    rounding_usd_input = fields.Float(string="USD to VND", tracking=True)
    rounding_jpy_input = fields.Float(string="JPY to VND", tracking=True)
    rounding_sgd_input = fields.Float(string="SGD to VND", tracking=True)
    
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    currency_usd = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self._get_default_currency('USD'), readonly=True)    
    currency_jpy = fields.Many2one('res.currency', string="YPY Currency", default=lambda self: self._get_default_currency('JPY'), readonly=True)   
    currency_sgd = fields.Many2one('res.currency', string="SGD Currency", default=lambda self: self._get_default_currency('SGD'), readonly=True)   
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)
    
    expense_usd = fields.Monetary(string="Total Expense", currency_field='currency_usd', store=True, compute="_convert_currency_revenue")
    expense_jpy = fields.Monetary(string="Total Expense", currency_field='currency_jpy', store=True, readonly=True)
    expense_sgd = fields.Monetary(string="Total Expense", currency_field='currency_sgd', store=True, readonly=True)
    expense_vnd = fields.Monetary(string="Total Expense", currency_field='currency_vnd', store=True, readonly=True)
    
    get_currency_name = fields.Char(string='Currency Name', readonly=True, store=True)
    
    @api.depends('total_expenses', 'rounding_usd_input', 'rounding_jpy_input', 'rounding_sgd_input', 'currency_id')
    def _convert_currency_revenue(self):
        for record in self:
            record.get_currency_name = record.currency_id.name
            if record.total_expenses != 0.0:
                if record.currency_id.name == 'VND':
                    record.expense_vnd = record.total_expenses
                    if record.rounding_usd_input != 0.0:
                        record.expense_usd = record.total_expenses / record.rounding_usd_input
                    else:
                        record.expense_usd = 0
                    if record.rounding_jpy_input != 0.0:
                        record.expense_jpy = record.total_expenses / record.rounding_jpy_input
                    else:
                        record.expense_jpy = 0
                    if record.rounding_sgd_input != 0.0:
                        record.expense_sgd = record.total_expenses / record.rounding_sgd_input
                    else:
                        record.expense_sgd = 0 
                        
                elif record.currency_id.name == 'JPY':   
                    record.expense_jpy = record.total_expenses
                    record.expense_vnd = record.total_expenses * record.rounding_jpy_input
                    # if record.rounding_usd_input != 0:
                    #     record.expense_usd = record.expense_vnd / record.rounding_usd_input
                    # else:
                    #     record.expense_usd = 0
                    
                elif record.currency_id.name == 'SGD':
                    record.expense_sgd = record.total_expenses
                    record.expense_vnd = record.total_expenses * record.rounding_sgd_input
                    
                else:
                    record.expense_usd = record.total_expenses
                    record.expense_vnd = record.total_expenses * record.rounding_usd_input
                    # record.expense_jpy = record.expense_vnd * record.rounding_jpy_input
            else:
                record.expense_usd = 0
                record.expense_jpy = 0
                record.expense_sgd = 0
                record.expense_vnd = 0
    
    
    @api.onchange('company_id')
    def _compute_project_company(self):
        if self.project_id.company_id.id != self.company_id.id:
            self.project_id = False


    @api.onchange('expense_date')
    def _validate_duration_expense_date(self):
        self.validate_project_expense_content(action = True)


    @api.onchange('project_id')
    def _validate_duration_project_expense(self):
        self.validate_project_expense_content(action = False)


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