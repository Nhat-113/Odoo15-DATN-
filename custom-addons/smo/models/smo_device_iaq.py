from odoo import models, fields, api

class SmoDeviceIaq(models.Model):
    _name = "smo.device.iaq"
    _description = "SmartOffice IAQ Devices"

    smo_device_id = fields.Many2one('smo.device', string="SmartOffice Device ID", required=True, ondelete='cascade')
    device_id = fields.Char(string="Device ID", required=True)
    device_name = fields.Char(string="Device Name")
    device_type= fields.Char(string="Device Type")
    param_name = fields.Char(string="Parameter", required=True, readonly=True)
    unit = fields.Char(string="Unit of Measurement", readonly=True, compute='_compute_unit')
    current_value = fields.Char(string="Current Value", required=True, readonly=True)
    last_updated = fields.Datetime(string="Last Updated", required=True, readonly=True)

    @api.depends('param_name')
    def _compute_unit(self):
        factor_to_unit = {
            'temperature': '°C',
            'humidity': '%RH',
            'sound': 'db',
            'co2': 'ppm',
            'co': 'ppm',
            'tvocs': 'ppm',
            'vocs': 'ppm',
            'pm2.5': 'ppm',
            'pm10': 'ppm',
            'pm1.0': 'ppm',
            'nh3': 'ppm',
            'nh4': 'ppm',
            'ch3': 'ppm',
            'ch4': 'ppm',
        }

        for record in self:
            record.unit = factor_to_unit.get(record.param_name.lower(), 'N/A')

