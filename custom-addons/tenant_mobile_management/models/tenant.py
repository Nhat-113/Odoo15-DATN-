# odoo/models/tenant.py
from odoo import models, fields, api

class Tenant(models.Model):
    _name = 'tenant.management'
    _description = "Tenat Mobile Management"
    _rec_name = "server_name"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"

    server_name = fields.Char(string= 'Server Name', required= True, tracking= True)
    link_domain = fields.Char(string= 'Link Domain', required= True, tracking= True)
    description = fields.Text(string= 'Description', tracking= True)
    sequence = fields.Integer(string= 'No.')
    allow_to_open = fields.Boolean(string= 'Allow To Open', default= False, tracking= True)
    device_ids = fields.One2many('device.information', 'tenant_id', string="devices")
    face_detection_link = fields.Char(string= 'Face Detection Link', tracking= True)
    box_username = fields.Char(string= 'Box User Name', tracking= True)
    box_password = fields.Char(string= 'Box Password', tracking= True)
    box_url = fields.Char(string= 'Box URL', tracking= True)

    @api.model
    def create(self, vals):
        if not vals.get('sequence'):
            last_sequence = self.search([], order='sequence desc', limit=1)
            vals['sequence'] = last_sequence.sequence + 1 if last_sequence else 1
        return super(Tenant, self).create(vals)

    def unlink(self):
        all_records = self.env['tenant.management'].search([], order='sequence')
        result = super(Tenant, self).unlink()
        all_records._update_sequences()
        return result

    @api.model
    def _update_sequences(self):
        tenants = self.search([], order='sequence')
        for index, tenant in enumerate(tenants):
            tenant.write({'sequence': index + 1})

    _sql_constraints = [
        ('server_name', 'unique(server_name)', 'Server name must be unique'),
    ]