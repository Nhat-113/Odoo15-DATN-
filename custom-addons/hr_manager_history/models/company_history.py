from odoo import models, fields

class CompanyHistory(models.Model):
    _name = 'hr.company.history'

    company_id = fields.Many2one('res.company', string="Department", readonly=True)
    date_start = fields.Datetime('Create Manager date', readonly=True)
    date_end = fields.Datetime('Change Manager date', readonly=True)
    email_history_id = fields.Char(string='Email Director history')  