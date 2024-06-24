from odoo import models, fields, api


class AttendanceDeviceDetailsApp(models.Model):
    _name = "attendance.device.details.app"
    _description = "HR attendance device details app"
    
    pseudo_attendance_id_app = fields.Many2one('hr.attendance.pesudo', string="Attendances", readonly=True)
    location_id = fields.Many2one('company.location',string="Location", readonly=True)
    