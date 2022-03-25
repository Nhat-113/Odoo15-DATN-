from odoo import api, fields, models

class ApplicationDate(models.Model):
    _inherit = 'hr.applicant'
    application_date = fields.Date(string='Application Date')

    recruitment_requester = fields.Many2many('hr.employee', string="Recruitment Requester", help="Employees who make a recruitment request.", copy=False)