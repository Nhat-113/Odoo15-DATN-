from odoo import models, fields

class DoorInformation(models.Model):
    _name = 'door.information'
    _description = "Door Information"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True )
    link = fields.Char(string="Link", required=True)
    tenant_id = fields.Many2one('tenant.management', string="Tenant")
