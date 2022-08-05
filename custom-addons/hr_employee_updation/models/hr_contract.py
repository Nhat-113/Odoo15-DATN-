from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class Contract(models.Model):
    _inherit = 'hr.contract'

    contract_old = fields.One2many('hr.contract.old', 'contract_id', string='Contract Old', compute='_get_contract_old', readonly=False)
    # @api.constrains('date_start', 'date_end')
    # def _check_dates(self):
    #     for contract in self:
    #         if contract.date_end:
    #             if contract.date_end and contract.date_start > contract.date_end:
    #                 raise ValidationError(_(
    #                     'Contract %(contract)s: start date (%(start)s) must be earlier than contract end date (%(end)s',
    #                     contract=contract.name, start=contract.date_start, end=contract.date_end
    #                 ))

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
        vals_olds = ['wage', 'non_taxable_allowance', 'taxable_allowance']
        salary_old = self.env['hr.contract'].search([('id', '=', self.id)])
        for vals_old in vals_olds:
            if vals_old in vals:
                self.env['hr.contract.old'].search([]).create({
                'contract_id' : self.id,
                'employee_id': self.employee_id.id,
                'salary_old': salary_old.wage + salary_old.non_taxable_allowance + salary_old.taxable_allowance,
                'date_expire': date.today()
                })
                break
        return super(Contract, self).write(vals)

    @api.depends('wage', 'non_taxable_allowance', 'taxable_allowance')
    def _get_contract_old(self):
        for old in self:
            old.contract_old = self.env['hr.contract.old'].search([('contract_id', '=', old.id)])

    @api.depends('state')
    def check_status_expired(self):
        if self.state == 'close':
            for contract in self.filtered(lambda c: not c.date_end):
                contract.date_end = max(date.today(), contract.date_start)
    
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