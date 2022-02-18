from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    seniority = fields.Char(compute='_compute_seniority', string='Employee Seniority')

    def _compute_seniority(self):
        for employee in self:
            diff = relativedelta(datetime.today(), employee['joining_date'])
            years = diff.years
            months = diff.months
            days = diff.days

            if years > 0:
                employee.seniority = '{} years {} months {} days'.format(years, months, days)
            elif months > 0:
                employee.seniority = '{} months {} days'.format(months, days)
            else:
                employee.seniority = '{} days'.format(days)

class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start:
            if self.employee_id:
                first_contract = self.employee_id._first_contract()
                if self.id.origin:
                    if first_contract.id == self.id.origin:
                        self.employee_id.joining_date = self.date_start