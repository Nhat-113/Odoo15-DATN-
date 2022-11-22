from odoo import api, models, _
from ...hr_payroll_community.models.hr_payslip import HrPayslip

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Pay Slip Inherit Support Service' 


    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):

        res = super(HrPayslip,self).get_worked_day_lines(contracts, self.date_from, self.date_to)

        for contract in contracts.filtered(lambda contract: contract.resource_calendar_id):
            if self.employee_id.user_id.id:
                total_tam_ung = 0
                luong_tam_ungs = self.env['support.services'].search([
                    ('flag_category', '=', 'tam_ung_luong'),
                    ('requester_id', '=', self.employee_id.user_id.id),
                    ('date_request', '>=', self.date_from),
                    ('date_request', '<=', self.date_to),
                    ('flag_status', '=', 'done')
                ])

                for luong in luong_tam_ungs:
                    total_tam_ung += luong.amount

                advance = {
                'name': _("Khấu trừ (VND)"),
                'sequence': 15,
                'code': 'LTU',
                'number_of_days': total_tam_ung,
                'contract_id': contract.id, 
                }

                res.append(advance)
        return res

        
