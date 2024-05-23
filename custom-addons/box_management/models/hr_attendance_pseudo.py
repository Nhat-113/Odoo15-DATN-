from odoo import models, fields, api
import pytz

class HrAttendancePseudo(models.Model):
    _inherit = "hr.attendance.pesudo"
    
    
    attendance_device_details = fields.One2many('attendance.device.details', 'pseudo_attendance_id', string="Attendance Device Details")
    is_multiple = fields.Boolean(string="Multiple")
    location_date = fields.Date("Location Date", store=True, compute="_compute_location_date")
    
    
    
    @api.depends('check_in', 'check_out')
    def _compute_location_date(self):
        user_tz = pytz.timezone(self.env.user.tz)
        for record in self:
            if record.check_in:
                record.location_date = record.check_in.astimezone(user_tz).date()
            elif not record.check_in and record.check_out:
                record.location_date = record.check_out.astimezone(user_tz).date()
            else:
                record.location_date = None
                
    def unlink(self):
        self.attendance_device_details.unlink()
        return super(HrAttendancePseudo, self).unlink()