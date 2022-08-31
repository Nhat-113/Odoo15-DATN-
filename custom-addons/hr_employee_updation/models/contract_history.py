from odoo import models, fields


class HrEmployeeContractHistory(models.Model):
    _name = 'hr.contract.old'
    _order = 'id desc'

    contract_id = fields.Many2one('hr.contract', string="Contract", readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)
    salary_old = fields.Float('Old Salary', readonly=True)
    date_expire = fields.Date('Expired Date', readonly=False)

    def unlink_salary_old(self):
        return super(HrEmployeeContractHistory, self).unlink()

    def write(self, vals):
        return super().write(vals)



        