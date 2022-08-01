from email.policy import default
from odoo import models, fields


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    company_id = fields.Many2one('res.company', string='Company', default=False)