from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar

class ExpenseManagement(models.Model):
    _name = "expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "General expense management"
    _rec_name = "description"
    _order = "start_date"
    
    start_date = fields.Date(string="Expenses Month", required=True, tracking=True)
    end_date = fields.Date(string="Expenses Month End", required=True, tracking=True)
    description = fields.Char(string="Expense Name", required=True, tracking=True)
    expense_generals = fields.One2many('expense.general', 'expense_management_id', string="General Expense")
    
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    total_expenses = fields.Monetary(string="Total Expenses", store=True, compute="_compute_total_expense_by_month", tracking=True)
    
    
    @api.depends('expense_generals')
    def _compute_total_expense_by_month(self):
        for record in self:
            record.total_expenses = sum(exp.total_expenses for exp in record.expense_generals)
    
    @api.onchange('start_date', 'end_date')
    def _validate_month(self):
        month_engs = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June', 
                     7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'}
        if self.start_date != False and self.end_date != False:
            last_days = calendar.monthrange(self.start_date.year, self.start_date.month)[1]
            if self.start_date.day != 1:
                raise UserError(_('The first day of the month must be equal to 1! Not %(day)s !', day = self.start_date.day))
            if self.end_date.day != last_days:
                month_letter = ''
                for mm in month_engs:
                    if mm == self.start_date.month:
                        month_letter = month_engs[mm]
                        break;
                raise UserError(_('The last day of %(month)s must be equal to %(last_day)s! Not %(day)s !', month = month_letter, last_day = last_days, day = self.end_date.day))

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