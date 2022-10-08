from odoo import api, fields, models, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    seniority_by_days = fields.Integer(compute='_compute_seniority_by_days', string='Seniority By Days', store=True)
    seniority = fields.Char(compute='compute_seniority', string='Employee Seniority', store=True)

    @api.onchange('contract_id')
    def compute_seniority(self):
        for employee in self.env['hr.employee'].search([]):
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

    def _compute_seniority_by_days(self):
        for employee in self:
            if isinstance(employee['joining_date'], (date)):
                diff = datetime.now().date() - employee['joining_date']
                employee.seniority_by_days = diff.days
            else:
                employee.seniority_by_days = 0
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