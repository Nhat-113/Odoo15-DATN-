from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
import json, babel.numbers

LIST_MONTHS = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
            ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
            ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')]
class ProjectRevenue(models.Model):
    _name = "project.revenue.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Revenue Management"
    _rec_name = "project_id"
    _order = 'company_id, project_id'
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])
    
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True)
    estimation_id = fields.Many2one('estimation.work', string="Estimation", related='project_id.estimation_id', store=True)
    
    start_date = fields.Date(string="Start date", related='project_id.date_start', store=True)
    end_date = fields.Date(string="End date", related='project_id.date', store=True)
    
    revenue_project = fields.Monetary(string="Total Revenue", currency_field='currency_id', compute='_compute_total_revenue', store=True, tracking=True)
    total_cost = fields.Float(string="Total Cost", related='project_id.estimation_id.total_cost', store=True)
    description = fields.Text(string="Description", tracking=True)
    
    rounding_usd_input = fields.Float(string="USD to VND", tracking=True)
    rounding_jpy_input = fields.Float(string="JPY to VND", tracking=True)
    rounding_sgd_input = fields.Float(string="SGD to VND", tracking=True)
    
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, store=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    currency_usd = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self._get_default_currency('USD'), readonly=True)    
    currency_jpy = fields.Many2one('res.currency', string="YPY Currency", default=lambda self: self._get_default_currency('JPY'), readonly=True)   
    currency_sgd = fields.Many2one('res.currency', string="SGD Currency", default=lambda self: self._get_default_currency('SGD'), readonly=True)
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)   
    
    revenue_usd = fields.Monetary(string="Total Revenue", currency_field='currency_usd', store=True, readonly=True, compute="_convert_currency_revenue")
    revenue_jpy = fields.Monetary(string="Total Revenue", currency_field='currency_jpy', store=True, readonly=True)
    revenue_sgd = fields.Monetary(string="Total Revenue", currency_field='currency_sgd', store=True, readonly=True)
    revenue_vnd = fields.Monetary(string="Total Revenue", currency_field='currency_vnd', store=True, readonly=True)
    
    get_currency_name = fields.Char(string='Currency Name', readonly=True, related='currency_id.name',store=True)
    get_domain_projects = fields.Char(string='Domain Project', readonly=True, store=False, compute='_get_domain_project')
    check_estimation = fields.Boolean(string="Check estimation", default=False, store=False)
    
    project_revenue_value_ids = fields.One2many('project.revenue.value', 'project_revenue_management_id', string='Project Revenue Value')

    # @api.depends('project_id','project_id.date_start','project_id.date')
    # def _compute_date_from_project(self):
    #     for record in self:
    #         project_revenues = self.env['project.revenue.management'].search_count([('id', '!=', record.id or record.id.origin), ('project_id', '=', record.project_id.id)])
    #         if project_revenues != 0:
    #             raise UserError(_('The project revenue "%(project)s" already exists!', project = record.project_id.name))
    
    
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
        if self.company_id.id != self.project_id.company_id.id:
            self.project_id = False
            self.project_revenue_value_ids = False
            
            
    @api.onchange('project_id')
    def _validate_project_revenue(self):
        get_datas = self.env['project.revenue.value'].search([('project_revenue_management_id', 'in', [self.id or self.id.origin, False]),
                                                              ('project_id', '=', self.project_id.id)])
        self.project_revenue_value_ids = get_datas
        for record in self.project_revenue_value_ids:
            if int(record.get_year) < self.project_id.date_start.year or int(record.get_year) > self.project_id.date.year or\
                int(record.get_month) < self.project_id.date_start.month or int(record.get_month) > self.project_id.date.month:
                    record.write({'project_expense_management_id': [(2, self.id or self.id.origin)]})
            
        if self.estimation_id:
            get_currency = self.env['res.currency'].search([('name', '=', self.estimation_id.currency_id.name)])
            self.currency_id = get_currency
            self.check_estimation = True
        else:
            self.check_estimation = False
            self.currency_id = self.env.ref('base.main_company').currency_id

    @api.depends('revenue_project', 'rounding_usd_input', 'rounding_jpy_input', 'rounding_sgd_input', 'currency_id')
    def _convert_currency_revenue(self):
        for record in self:
            # record.get_currency_name = record.currency_id.name
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
                
                elif record.currency_id.name == 'SGD':
                    record.revenue_sgd = record.revenue_project
                    record.revenue_vnd = record.revenue_project * record.rounding_sgd_input
                    
                else:
                    record.revenue_usd = record.revenue_project
                    record.revenue_vnd = record.revenue_project * record.rounding_usd_input
            else:
                record.revenue_usd = 0
                record.revenue_jpy = 0
                record.revenue_sgd = 0
                record.revenue_vnd = 0

        
    @api.depends('project_revenue_value_ids.revenue_project')
    def _compute_total_revenue(self):
        for record in self:
            total_revenue = sum(item.revenue_project for item in record.project_revenue_value_ids)
            if record.estimation_id and total_revenue > record.total_cost:
                    raise UserError(_('Project revenue must not be greater than total cost estimate "%(total_cost)s %(currency)s" ', 
                                    total_cost = babel.numbers.format_currency( record.total_cost, '' ), currency = record.currency_id.name))
            else:
                record.revenue_project = total_revenue
            
            
    @api.onchange('project_revenue_value_ids')
    def _validate_new_record(self):
        months = [(record.get_month, record.get_year) for record in self.project_revenue_value_ids]
        month_unique = []
        for index, value in months:
            if (index, value) not in [(item, data) for item, data in month_unique]:
                month_unique.append((index, value))
            else:
                month_eng = ''
                for item in LIST_MONTHS:
                    if item[0] == index:
                        month_eng = item[1]
                        break
                raise UserError(_('The "%(month)s %(year)s" of project "%(project)s" already exists!',
                        month = month_eng, year = value, project = self.project_id.name))
            
    def unlink(self):
        for record in self:
            record.project_revenue_value_ids.unlink()
        return super(ProjectRevenue, self).unlink()
    
    
    def action_open_estimation(self):
        action = {
            'name': self.project_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'estimation.work',
            'view_ids': self.env.ref('ds_project_estimation.action_estimation_work').id,
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.estimation_id.id)]
        }
        return action
                    
class ProjectRevenueValue(models.Model):
    _name = 'project.revenue.value'
    _order = 'sort_date desc'
    
    
    def _get_years(self):
        return self.env['expense.management']._get_years()
    
    def _get_year_defaults(self):
        return self.env['expense.management']._get_year_defaults()
    
    def _get_month_defaults(self):
        return self.env['expense.management']._get_month_defaults()
    
    project_revenue_management_id = fields.Many2one('project.revenue.management', string="Project Revenue Management")

    get_month = fields.Selection(selection=LIST_MONTHS,
                                    # default=_get_month_defaults,
                                    string="Month",
                                    required=True)
    get_year = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Year', required=True)
    
    sort_date = fields.Date(string="Soft Date", store=True)
    revenue_project = fields.Monetary(string="Total Revenue", currency_field='currency_id', required=True)
    description = fields.Text(string="Description")
    
    project_id = fields.Many2one('project.project', string="Project", related="project_revenue_management_id.project_id", store=True)
    currency_id = fields.Many2one('res.currency', string="Currency", related='project_revenue_management_id.currency_id', store=True)
    
    
    @api.onchange('get_month', 'get_year')
    def _validate_stage_project(self):
        if self.project_revenue_management_id.project_id.id:
            self._validate_content(action = True)
            
    @api.onchange('project_id')
    def _validate_project(self):
        for record in self:
            record._validate_content(action = False)

    def _validate_content(self, action):
        if self.project_id.date == False or self.project_id.date_start == False:
            if action == True:
                raise UserError(_('The duration of the project is false! Please update duration of project "%(project)s"', 
                                    project = self.project_id.name))
            # else:
            #     self.write({'project_revenue_management_id': [(2, self.id or self.id.origin)]})
                    
        if self.get_year and self.get_month:
            if int(self.get_year) < self.project_id.date_start.year or int(self.get_year) > self.project_id.date.year or\
                int(self.get_month) < self.project_id.date_start.month or int(self.get_month) > self.project_id.date.month:
                    if action == True:
                        raise UserError(_('The month "%(month)s/%(year)s" is outside the project implementation period "%(project)s" !',
                                    month = '0' + self.get_month if int(self.get_month) < 10 else self.get_month,
                                    year = self.get_year, project = self.project_id.name))
                    # else:
                    #     self.write({'project_revenue_management_id': [(2, self.id or self.id.origin)]})
            else:
                self.sort_date = datetime.strptime(('01' + '/' + self.get_month + '/' + self.get_year), '%d/%m/%Y')
