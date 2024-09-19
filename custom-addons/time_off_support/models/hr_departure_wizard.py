from odoo import models, fields
from odoo.exceptions import UserError

class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'
    def action_register_departure(self):
        if self.cancel_leaves:
            future_leaves_date = self.env['hr.leave'].search([
                ('employee_id', '=', self.employee_id.id),
                ('date_to', '>=', self.departure_date),
                ('date_from', '<=', self.departure_date),
                ('state', '=', 'validate') 
            ])

            if future_leaves_date:
                raise UserError("The contract end date falls within the employee's approved leave.")
        super(HrDepartureWizard, self).action_register_departure()
