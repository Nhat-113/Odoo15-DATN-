from odoo import models, fields, api



class ProjectRevenue(models.Model):
    _name = "project.revenue.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Revenue Management"
    _rec_name = "project_id"
    _order = "id DESC"
    
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    
    start_date = fields.Date(string="Start date", required=True, tracking=True)
    end_date = fields.Date(string="End date", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    revenue_project = fields.Monetary(string="Total Revenue", currency_field='currency_id', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, readonly=True, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    
    rounding_usd_input = fields.Monetary(string="USD", currency_field='currency_id', tracking=True)
    rounding_jpy_input = fields.Monetary(string="JPY", currency_field='currency_id', tracking=True)
    
    currency_usd = fields.Many2one('res.currency', string="USD Currency", default=lambda self: self._get_default_currency('USD'), readonly=True)    
    currency_jpy = fields.Many2one('res.currency', string="YPY Currency", default=lambda self: self._get_default_currency('JPY'), readonly=True)   
    
    revenue_usd = fields.Monetary(string="Total Revenue (USD)", currency_field='currency_usd', store=True, compute="_convert_currency_revenue")
    revenue_jpy = fields.Monetary(string="Total Revenue (JPY)", currency_field='currency_jpy', store=True, readonly=True)


    @api.depends('revenue_project', 'rounding_usd_input', 'rounding_jpy_input')
    def _convert_currency_revenue(self):
        if self.revenue_project != 0.0:
            if self.rounding_usd_input != 0.0:
                self.revenue_usd = self.revenue_project / self.rounding_usd_input
            if self.rounding_jpy_input != 0.0:
                self.revenue_jpy = self.revenue_project / self.rounding_jpy_input

    
    @api.onchange('company_id')
    def _compute_project_company(self):
        if self.company_id.id != self.project_id.company_id.id:
            self.project_id = False