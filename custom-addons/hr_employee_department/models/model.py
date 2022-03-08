from odoo import models, fields, api

class Model(models.Model):
    _inherit = "hr.department"
    name = fields.Char(string ='Department Name', required = True)
    
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Department name must be unique!'),
    ]