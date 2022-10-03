from odoo import models, fields

class CompanyHistory(models.Model):
    _name = 'hr.company.history'

    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    date_start = fields.Date('Date Start', readonly=False)
    date_end = fields.Date('Date End', readonly=False)
    email_history_id = fields.Char(string='Email Representative History')
    representative = fields.Many2one('hr.employee', "Representative")