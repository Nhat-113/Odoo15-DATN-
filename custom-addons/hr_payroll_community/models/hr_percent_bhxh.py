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

    def re_compute_percent_bhxh(self):
        gross_id = self.env['hr.payroll.structure'].search([('code', '=', 'BASE2')]).id
        for payslip in self.env['hr.payslip'].search([('struct_id', '=', gross_id)]):
            input_bhxh_sdld = self.env['hr.payslip.input'].search([('payslip_id', '=', payslip.id), ('code', '=', 'BHC')])
            if len(input_bhxh_sdld) == 0:
                self.env['hr.payslip.input'].create({
                    'name': 'BHXH (%) (của SDLĐ)',
                    'code': 'BHC',
                    'amount': 21.5,
                    'contract_id': payslip.contract_id.id,
                    'payslip_id': payslip.id
                })
            input_bhxh = self.env['hr.payslip.input'].search([('payslip_id', '=', payslip.id), ('code', '=', 'PBH')])
            if len(input_bhxh) == 0:
                self.env['hr.payslip.input'].create({
                    'name': 'BHXH (%) (của NLĐ)',
                    'code': 'PBH',
                    'amount': 10.5,
                    'contract_id': payslip.contract_id.id,
                    'payslip_id': payslip.id
                })
            payslip.compute_sheet()