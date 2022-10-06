from odoo import api, models, fields

class CompanyHistory(models.Model):
    _name = 'hr.company.history'

    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    date_start = fields.Date('Date Start', readonly=False)
    date_end = fields.Date('Date End', readonly=False)
    email_history_id = fields.Char(string='Email Representative History', compute="_compute_email_with_representative", store=True)
    representative = fields.Many2one('hr.employee', "Representative")

    @api.depends('representative')
    def _compute_email_with_representative(self):
        for record in self:
            record.email_history_id = self.env['hr.employee'].search([('id','=',record.representative.id)]).work_email
