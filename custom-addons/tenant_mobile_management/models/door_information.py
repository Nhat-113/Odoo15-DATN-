from odoo import models, fields

class DoorInformation(models.Model):
    _name = 'door.information'
    _description = "Door Information"
    _rec_name = "door_name"

    door_name = fields.Char(string="Door Name", required=True, tracking=True)
    door_link = fields.Char(string="Door Link", required=True, tracking=True)
    tenant_id = fields.Many2one('tenant.management', string="Tenant")
