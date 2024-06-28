from datetime import date, datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class LocationWifi(models.Model):
    _name = 'location.wifi'
    _description = "Location Wifi"
    _rec_name = 'ssid'

    name = fields.Char("Name", required=True, size=100)
    ssid= fields.Char("SSID", required=True, size=32)
    parent_id = fields.Many2one('company.location', string='Parent')

    _sql_constraints = [
        ('unique_ssid_per_parent', 'UNIQUE(ssid)', 'The SSID already exists.')
    ]