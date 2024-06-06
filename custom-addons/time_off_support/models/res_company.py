from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    time_off_type_id = fields.Many2one('hr.leave.type', string='For Work From Home')