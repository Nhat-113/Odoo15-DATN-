from odoo import models, fields


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    is_multiple = fields.Boolean(string="Multiple")
    