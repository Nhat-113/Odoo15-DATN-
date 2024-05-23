from odoo import models, fields, api


class AttendanceDeviceDetails(models.Model):
    _name = "attendance.device.details"
    _description = "HR attendance device details"
    
    
    pseudo_attendance_id = fields.Many2one('hr.attendance.pesudo', string="Attendances", readonly=True)
    device_id = fields.Many2one('box.management', string="Device", readonly=True)
    device_type = fields.Selection(related='device_id.device_type', string="Device Type", readonly=True, store=True)
    position = fields.Text(string="Position", readonly=True)
    
    