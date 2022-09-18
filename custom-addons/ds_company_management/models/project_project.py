from odoo import api, fields, models, _

class Project(models.Model):
    _inherit = 'project.project'
    
    div_manager = fields.Many2one('hr.employee', string='Division Manager', required=True)