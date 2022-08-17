from odoo import models, fields, api



class ProjectExpense(models.Model):
    _name = "project.expense.management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Project Expense Management"
    _rec_name = "name"
    _order = "id DESC"
    
    
    name = fields.Char(string="Expense name", required=True, tracking=True)
    expense_date = fields.Date(string="Expense Date", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    total_expenses = fields.Monetary(string="Total Expenses", required=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id, tracking=True)
    description = fields.Text(string="Description", tracking=True)