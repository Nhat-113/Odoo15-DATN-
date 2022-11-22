from odoo import api, fields, models
from odoo.exceptions import UserError

class HrPercentBHXH(models.Model):
    _name = 'hr.percent.bhxh'
    _description = 'Percent BHXH'

    name = fields.Char(string='Name', required=True, readonly=True)
    type_percent = fields.Char(string='type_percent', required=True, readonly=True)
    percent = fields.Float(string='%', required=True)

    @api.constrains('percent')
    def _check_percent_bhxh(self):
        for record in self:
            if record.percent <= 0 or record.percent > 100:
                raise UserError('Percent must not be less than 0 and greater than 100')