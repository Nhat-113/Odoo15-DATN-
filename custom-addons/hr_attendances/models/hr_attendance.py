from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = "id desc"

    check_in = fields.Datetime(string="Check In", required=False)

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        # TODO create check validity func here
        return True