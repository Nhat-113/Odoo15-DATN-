from odoo import fields, models, tools


class ProjectManagementSubCeo(models.Model):
    _name = 'project.management.subceo'
    _description = 'Project Management Sub CEO'
    _auto = False
    
    
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr_department', string='Department')
    total_members = fields.Float(string='Members')
    total_salary = fields.Monetary(string="Salary Cost")
    total_project_cost = fields.Monetary(string="Project Cost")
    total_revenue = fields.Monetary(string="Revenue")
    total_profit = fields.Monetary(string="Profit")