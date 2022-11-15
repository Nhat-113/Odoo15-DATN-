from odoo import models, fields, api, _
from odoo.exceptions import UserError
import calendar
from datetime import date, datetime


LIST_MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]

COUNT_RECURSIVES = 0

class ExpenseManagement(models.Model):
    _name = "expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "General expense management"
    _rec_name = "description"
    _order = "company_id, sort_date desc"
    
    def _get_years(self):
        year_list = []
        for i in range(date.today().year - 10, date.today().year + 10):
            year_list.append((str(i), str(i)))
        return year_list
    
    def _get_year_defaults(self):
        return str(date.today().year)
    
    def _get_month_defaults(self):
        return str(date.today().month)
    
    def _get_default_sort_date(self):
        # Because server production data already exists then have must be to update field sort_date for sort feature
        datas = self.search([('sort_date', '=', False)])
        if datas:
            for record in datas:
                record.sort_date = datetime.strptime(('01' + '/' + record.get_month + '/' + record.get_year), '%d/%m/%Y')
        for item in self:
            item.sort_date = False

    
    get_month = fields.Selection(selection=LIST_MONTHS, string="Month", required=True, tracking=True)
    get_year = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Year', required=True, tracking=True)
    sort_date = fields.Date(string="Soft Date", default=_get_default_sort_date)
    description = fields.Char(string="Expense Name", required=True, tracking=True)
    total_expenses = fields.Float(string="Total Expenses", store=True, compute="_compute_total_expense_by_month", tracking=True)
    
    company_id = fields.Many2many('res.company', 'general_expenses_company_rel', string="Companies", default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    
    expense_generals = fields.One2many('expense.general', 'expense_management_id', string="General Expense")
    expenses_activities= fields.One2many('expense.activity', 'expense_management_id', string="Activity Expense")
    
    
    def write(self, vals):
        if 'company_id' in vals:
            #tracking many2many field
            company_before = self._get_company_name(self.company_id)
            companies = self.env['res.company'].search([('id', 'in', vals['company_id'][0][-1])])
            company_after = self._get_company_name(companies)
            if company_before == '':
                company_before = 'None'
            if company_after == '':
                company_after = 'None'
            message = "Company: " + company_before + " --> " + company_after
            self.message_post(body=message)
            
        result = super(ExpenseManagement, self).write(vals)
        return result
    
    
    @api.onchange('get_month', 'get_year')
    def _validate_get_month(self):
        if self.get_month and self.get_year:
            datas = self.search([('id', '!=', self.id or self.id.origin), ('company_id', 'in', self.company_id.ids), ('get_year', '=', self.get_year)])
            check = False
            if datas:
                for item in datas:
                    if self.get_month == item.get_month:
                        raise UserError(_('The operation cost month "%(month)s/%(year)s" of %(company)s already exist !',
                                            month = '0' + self.get_month if int(self.get_month) < 10 else self.get_month,
                                            year = self.get_year, company = self._get_company_name(self.company_id)))
                    else:
                        check = True
                if check == True:
                    self.sort_date = datetime.strptime(('01' + '/' + self.get_month + '/' + self.get_year), '%d/%m/%Y')
            else:
                self.sort_date = datetime.strptime(('01' + '/' + self.get_month + '/' + self.get_year), '%d/%m/%Y')


    def _get_company_name(self, companies):
        if len(companies) == 1:
            return companies.name
        else:
            company_name = ''
            cnt = 0
            for record in companies:
                cnt += 1
                rel = ''
                if cnt <= len(companies) - 1:
                    rel += ', '
                company_name += record.name + rel
                
            return company_name
            
    @api.depends('expense_generals', 'expenses_activities')
    def _compute_total_expense_by_month(self):
        for record in self:
            record.total_expenses = sum(exp.total_expenses for exp in record.expense_generals) + \
                                    sum(exp.total_expenses for exp in record.expenses_activities)
    
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = default or {}
        new_expense_management = super(ExpenseManagement, self).copy(default)
        
        result_check = self._check_month_copy(new_expense_management.id, 
                                            int(self.get_month) + 1 if int(self.get_month) < 12 else 1, 
                                            int(self.get_year) if int(self.get_month) < 12 else int(self.get_year) + 1)
        if result_check['check'] == False:
            raise UserError(_("The data cannot be copied because the data is too old or too far away from present! Let's create a new operation cost"))
        else:
            new_expense_management.get_month = result_check['next_month']
            new_expense_management.get_year = result_check['next_year']
            new_expense_management.sort_date = datetime.strptime(('01' + '/' + result_check['next_month'] + '/' + result_check['next_year']), '%d/%m/%Y')
        
            for exp_gen in self.expense_generals:
                exp_gen.copy(default={'expense_management_id': new_expense_management.id})
                
            for exp_act in self.expenses_activities:
                exp_act.copy(default={'expense_management_id': new_expense_management.id})
                
            return new_expense_management
    
    
    def _check_month_copy(self, new_record_id, next_month, next_year):
        global COUNT_RECURSIVES
        datas = self.search([('id', '!=', new_record_id), 
                            ('company_id', 'in', self.company_id.ids), 
                            ('get_year', '=', str(next_year)), 
                            ('get_month', '=', str(next_month))])
        if not datas:
            COUNT_RECURSIVES = 0
            if next_year < date.today().year + 10:
                return {'check': True, 'next_month': str(next_month), 'next_year': str(next_year)}
            else:
                return {'check': False, 'next_month': '', 'next_year': ''}
        else:
            # max loop is 10 year = 10*12 ~ 120 loop
            if COUNT_RECURSIVES == 119:
                COUNT_RECURSIVES = 0
                return {'check': False, 'next_month': '', 'next_year': ''}
            else:
                COUNT_RECURSIVES += 1
                if next_month == 12:
                    next_month = 1
                    next_year += 1
                else:
                    next_month += 1
                return self._check_month_copy(new_record_id, next_month, next_year)
    
    def unlink(self):
        for record in self:
            record.expense_generals.unlink()
            record.expenses_activities.unlink()
        return  super(ExpenseManagement, self).unlink()

class ExpenseGeneral(models.Model):
    """ This is Activity Expenses model in UI end user Because server production, data already exists so can't modify model name
    """
    _name = 'expense.general'
    _description = "General Expense"
    _rec_name = "category_expenses"
    _order = "category_expenses"
    
    expense_management_id = fields.Many2one('expense.management', string="Expense Management")
    category_expenses = fields.Many2one('expense.general.category', string="Category", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related="expense_management_id.currency_id")
    total_expenses = fields.Float(string="Expense")
    description = fields.Text(string="Description")
    
    
    
class ActivityExpense(models.Model):
    """ This is General Expenses model in UI end user
    """
    _name = 'expense.activity'
    _description = "Activity Expense"
    _rec_name = "category_expenses"
    _order = "category_expenses"
    
    expense_management_id = fields.Many2one('expense.management', string="Expense Management")
    category_expenses = fields.Many2one('expense.general.category', string="Category", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related="expense_management_id.currency_id")
    total_expenses = fields.Float(string="Expense")
    description = fields.Text(string="Description")