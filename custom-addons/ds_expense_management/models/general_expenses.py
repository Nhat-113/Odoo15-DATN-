from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar
from datetime import date

class ExpenseManagement(models.Model):
    _name = "expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "General expense management"
    _rec_name = "description"
    _order = "id"
    
    def _get_years(self):
        year_list = []
        for i in range(2010, 2051):
            year_list.append((str(i), str(i)))
        return year_list
    
    def _get_year_defaults(self):
        return str(date.today().year)
    
    def _get_month_defaults(self):
        return str(date.today().month)
        
    
    get_month = fields.Selection([('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                                    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                                    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')],
                                default=_get_month_defaults,
                                string="Month",
                                required=True,
                                tracking=True)
    get_year = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Year', required=True, tracking=True)
    
    description = fields.Char(string="Expense Name", required=True, tracking=True)
    expense_generals = fields.One2many('expense.general', 'expense_management_id', string="General Expense")
    
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    total_expenses = fields.Monetary(string="Total Expenses", store=True, compute="_compute_total_expense_by_month", tracking=True)
    
    
    @api.depends('expense_generals')
    def _compute_total_expense_by_month(self):
        for record in self:
            record.total_expenses = sum(exp.total_expenses for exp in record.expense_generals)
    
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        new_expense_management = super(ExpenseManagement, self).copy(default)
        for exp_gen in self.expense_generals:
            exp_gen.copy(default={'expense_management_id': new_expense_management.id})
        return new_expense_management
    
    
    def unlink(self):
        for record in self:
            record.expense_generals.unlink()
        return  super(ExpenseManagement, self).unlink()

class ExpenseGeneral(models.Model):
    _name = 'expense.general'
    _description = "General Expense"
    _rec_name = "category_expenses"
    _order = "category_expenses"
    
    expense_management_id = fields.Many2one('expense.management', string="Expense Management")
    category_expenses = fields.Many2one('expense.general.category', string="Category", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related="expense_management_id.currency_id")
    total_expenses = fields.Monetary(string="Expense")
    description = fields.Text(string="Description")