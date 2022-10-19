from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime

List_month = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]
class ProjectRevenue(models.Model):
    _name = "project.revenue.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Revenue Management"
    _rec_name = "project_id"
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])
    
    def _get_years(self):
        return self.env['expense.management']._get_years()
    
    def _get_year_defaults(self):
        return self.env['expense.management']._get_year_defaults()
    
    def _get_month_defaults(self):
        return self.env['expense.management']._get_month_defaults()


    start_date = fields.Date(string="Start date", required=False, tracking=True, compute='_compute_date_from_project', store=True)
    end_date = fields.Date(string="End date", required=False, tracking=True, compute='_compute_date_from_project', store=True)
    
    get_month = fields.Selection(selection=List_month,
                                    default=_get_month_defaults,
                                    string="Month",
                                    required=True,
                                    tracking=True)
    get_year = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Year', required=True, tracking=True)
    
    show_date = fields.Char(string="Month")
    sort_date = fields.Date(string="Soft Date")
    
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    revenue_project = fields.Monetary(string="Total Revenue", currency_field='currency_id', required=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    
    rounding_usd_input = fields.Float(string="USD to VND", tracking=True)
    rounding_jpy_input = fields.Float(string="JPY to VND", tracking=True)
    rounding_sgd_input = fields.Float(string="SGD to VND", tracking=True)
    
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    currency_usd = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self._get_default_currency('USD'), readonly=True)    
    currency_jpy = fields.Many2one('res.currency', string="YPY Currency", default=lambda self: self._get_default_currency('JPY'), readonly=True)   
    currency_sgd = fields.Many2one('res.currency', string="SGD Currency", default=lambda self: self._get_default_currency('SGD'), readonly=True)
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)   
    
    revenue_usd = fields.Monetary(string="Total Revenue", currency_field='currency_usd', store=True, readonly=True, compute="_convert_currency_revenue")
    revenue_jpy = fields.Monetary(string="Total Revenue", currency_field='currency_jpy', store=True, readonly=True)
    revenue_sgd = fields.Monetary(string="Total Revenue", currency_field='currency_sgd', store=True, readonly=True)
    revenue_vnd = fields.Monetary(string="Total Revenue", currency_field='currency_vnd', store=True, readonly=True)
    
    get_currency_name = fields.Char(string='Currency Name', readonly=True, store=True)

    @api.depends('project_id','project_id.date_start','project_id.date')
    def _compute_date_from_project(self):
        for record in self:
            record.start_date = record.project_id.date_start
            record.end_date = record.project_id.date

    @api.depends('revenue_project', 'rounding_usd_input', 'rounding_jpy_input', 'rounding_sgd_input', 'currency_id')
    def _convert_currency_revenue(self):
        for record in self:
            record.get_currency_name = record.currency_id.name
            if record.revenue_project != 0.0:
                if record.currency_id.name == 'VND':
                    record.revenue_vnd = record.revenue_project
                    if record.rounding_usd_input != 0.0:
                        record.revenue_usd = record.revenue_project / record.rounding_usd_input
                    else:
                        record.revenue_usd = 0
                    if record.rounding_jpy_input != 0.0:
                        record.revenue_jpy = record.revenue_project / record.rounding_jpy_input
                    else:
                        record.revenue_jpy = 0
                    if record.rounding_sgd_input != 0.0:
                        record.revenue_sgd = record.revenue_project / record.rounding_sgd_input
                    else:
                        record.revenue_sgd = 0 
                        
                elif record.currency_id.name == 'JPY':   
                    record.revenue_jpy = record.revenue_project
                    record.revenue_vnd = record.revenue_project * record.rounding_jpy_input
                    # if record.rounding_usd_input != 0:
                    #     record.revenue_usd = record.revenue_vnd / record.rounding_usd_input
                    # else:
                    #     record.revenue_usd = 0
                
                elif record.currency_id.name == 'SGD':
                    record.revenue_sgd = record.revenue_project
                    record.revenue_vnd = record.revenue_project * record.rounding_sgd_input
                    
                else:
                    record.revenue_usd = record.revenue_project
                    record.revenue_vnd = record.revenue_project * record.rounding_usd_input
                    # record.revenue_jpy = record.revenue_vnd * record.rounding_jpy_input
            else:
                record.revenue_usd = 0
                record.revenue_jpy = 0
                record.revenue_sgd = 0
                record.revenue_vnd = 0
        
    @api.onchange('company_id')
    def _compute_project_company(self):
        if self.company_id.id != self.project_id.company_id.id:
            self.project_id = False
            
    @api.onchange('get_month', 'get_year')
    def _validate_stage_project(self):
        if self.project_id.id:
            self._validate_content(action = True)
            
    @api.onchange('project_id')
    def _validate_project(self):
        self._validate_content(action = False)

    def _validate_content(self, action):
        if self.project_id.date == False or self.project_id.date_start == False:
            if action == True:
                raise UserError(_('The duration of the project is false! Please update duration of project "%(project)s"', 
                                    project = self.project_id.name))
            else:
                self.get_month = ''
                    
        if self.get_year and self.get_month:
            if int(self.get_year) < self.start_date.year or int(self.get_year) > self.end_date.year or\
                int(self.get_month) < self.start_date.month or int(self.get_month) > self.end_date.month:
                    if action == True:
                        raise UserError(_('The month "%(month)s/%(year)s" is outside the project implementation period "%(project)s" !',
                                    month = '0' + self.get_month if int(self.get_month) < 10 else self.get_month,
                                    year = self.get_year, project = self.project_id.name))
                    else:
                        self.get_month = ''
            else:
                self.sort_date = datetime.strptime(('01' + '/' + self.get_month + '/' + self.get_year), '%d/%m/%Y')
                for item in List_month:
                    if item[0] == self.get_month:
                        self.show_date = self.get_year + ' ' + item[1]
                        break