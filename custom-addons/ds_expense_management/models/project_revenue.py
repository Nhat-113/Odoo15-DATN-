from odoo import models, fields, api



class ProjectRevenue(models.Model):
    _name = "project.revenue.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Revenue Management"
    _rec_name = "project_id"
    _order = "id DESC"
    
    
    start_date = fields.Date(string="Start date", required=True, tracking=True)
    end_date = fields.Date(string="End date", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    revenue_project = fields.Monetary(string="Total Revenue", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    description = fields.Text(string="Description", tracking=True)