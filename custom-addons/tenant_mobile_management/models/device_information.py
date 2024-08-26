from odoo import models, fields

class DeviceInformation(models.Model):
    _name = 'device.information'
    _description = "Device Information"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True )
    device_id = fields.Char(string="ID", required=True)
    description = fields.Text(string= 'Description')
    tenant_id = fields.Many2one('tenant.management', string="Tenant")
