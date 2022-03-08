from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class Contract(models.Model):
    _inherit = 'hr.contract'

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for contract in self:
            if contract.date_end and contract.date_start > contract.date_end or contract.date_end < date.today():
                raise ValidationError(_(
                    'Contract %(contract)s: start date (%(start)s) must be earlier than contract end date (%(end)s) and end date (%(end)s) must be later than today (%(today)s)',
                    contract=contract.name, start=contract.date_start, end=contract.date_end, today=date.today()
                ))

    def _assign_open_contract(self):
        for contract in self:
            if contract.date_end >= date.today():
                contract.employee_id.sudo().write({'contract_id': contract.id})
            else:
                raise ValidationError(_('Contract has expired on day(%(date_end)s)', date_end=contract.date_end))

    def write(self, vals):
        res = super(Contract, self).write(vals)
        if vals.get('state') == 'open' or 'draft':
            self._assign_open_contract()
        
        return res