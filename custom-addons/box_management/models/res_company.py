from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    attendance_view_type = fields.Boolean(string="Attendance view multiple records", default=False)
    
    