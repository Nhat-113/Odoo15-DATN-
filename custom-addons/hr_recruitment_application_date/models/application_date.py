from odoo import api, fields, models

class ApplicationDate(models.Model):
    _inherit = 'hr.applicant'
    application_date = fields.Date(string='Application Date')