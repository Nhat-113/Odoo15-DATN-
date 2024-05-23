# odoo/models/tenant.py
from odoo import models, fields

class Tenant(models.Model):
    _name = 'tenant.management'
    _description = "Tenat Mobile Management"
    _rec_name = "server_name"
    _order = "id"

    server_name = fields.Char(string='Server Name', required=True)
    link_domain = fields.Char(string='Link Domain', required=True)
    description = fields.Text(string='Description')

    _sql_constraints = [
        ('server_name', 'unique(server_name)', 'Server name must be unique'),
    ]