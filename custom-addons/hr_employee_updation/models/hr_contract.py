from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class Contract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for contract in self:
            if contract.date_end:
                if contract.date_end and contract.date_start > contract.date_end or contract.date_end < date.today():
                    raise ValidationError(_(
                        'Contract %(contract)s: start date (%(start)s) must be earlier than contract end date (%(end)s) and end date (%(end)s) must be later than today (%(today)s)',
                        contract=contract.name, start=contract.date_start, end=contract.date_end, today=date.today()
                    ))

    @api.constrains('employee_id')
    def _check_employee(self):
        if not self.employee_id:
            raise ValidationError(_(
                    'Please choose an employee for the contract.'
                ))

    @api.onchange('state')
    def onchage_state(self):
        if self.state == 'cancel':
            payslips = [payslip for payslip in self.env['hr.payslip'].search(['&', ('employee_id', '=', self.employee_id.id), ('state', '!=', 'done')])]
            for payslip in payslips:
                payslip.write({'state': 'cancel'})
        return

    @api.model
    def create(self, vals):
        contracts = super(Contract, self).create(vals)
        if vals.get('state') == 'open':
            contracts._assign_open_contract()
        if vals.get('state') == 'close':
            if not contracts.date_end:
                contracts.date_end = max(date.today(), contracts.date_start)
        open_contracts = contracts.filtered(lambda c: c.state == 'open' or c.state == 'draft' and c.kanban_state == 'done')
        # sync contract calendar -> calendar employee
        for contract in open_contracts.filtered(lambda c: c.employee_id and c.resource_calendar_id):
            contract.employee_id.resource_calendar_id = contract.resource_calendar_id
        return contracts

    def write(self, vals):
        res = super(Contract, self).write(vals)
        if self.state == 'close':
            for contract in self.filtered(lambda c: not c.date_end):
                contract.date_end = max(date.today(), contract.date_start)

        return res

    # def _assign_open_contract(self):
    #     for contract in self:
    #         if contract.date_end:
    #             if contract.date_end >= date.today():
    #                 contract.employee_id.sudo().write({'contract_id': contract.id})
    #             else:
    #                 raise ValidationError(_('Contract has expired on day(%(date_end)s)', date_end=contract.date_end))

    # def write(self, vals):
    #     res = super(Contract, self).write(vals)
    #     if vals.get('state') == 'open' or 'draft':
    #         self._assign_open_contract()
        
    #     return res
