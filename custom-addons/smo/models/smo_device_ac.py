from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.http import request
from helper.smo_helper import make_request
import requests
import json
import logging

_logger = logging.getLogger('smo.logger')

class SmoDeviceAc(models.Model):
    _name = "smo.device.ac"
    _description = "SmartOffice AC device"
    _order = 'name asc'

    name = fields.Char(string="AC Name", default=lambda ac: ac.device_name)
    
    smo_device_id = fields.Many2one('smo.device', string="SmartOffice Device ID", required=True, ondelete='cascade')
    
    asset_name = fields.Char(string="Asset Name", related="smo_device_id.asset_name")
    
    device_id = fields.Char(string="Device ID", related="smo_device_id.device_id")
    device_name = fields.Char(string="Device Name", related="smo_device_id.device_name")
    device_type= fields.Char(string="Device Type", related="smo_device_id.device_type")
    
    power_state = fields.Boolean(string="Power ON/OFF", required=True)
    temperature = fields.Integer(string="Temperature", required=True, help="Temperature in °C: 17°C ➜ 30°C")
    
    mode = fields.Selection([
        ('0', 'Auto'),
        ('1', 'Cool'),
        ('2', 'Dry'),
        ('3', 'Heat'),
        ('4', 'Fan')
    ], string="Mode", required=True, default='0')
    
    fan_speed = fields.Selection([
        ('3', 'Auto'),
        ('0', 'Low'),
        ('1', 'Medium'),
        ('2', 'High'),
    ], string="Fan Speed", required=True, default='0')
    
    def _get_keys_to_fields_mapping(self):
        return {
            'temp': 'temperature',
            'mode': 'mode',
            'fanSpeed': 'fan_speed',
            'powerState': 'power_state'
            
        }   
    
    @api.constrains('temperature')
    def _validate_temperature(self):
        for record in self:
            if not (17 <= record.temperature <= 30):
                raise UserError("Temperature should be between 17°C and 30°C")
            
    @api.model
    def create(self, vals):
        crr_username = self.env.user.name
        changing_message = ', '.join([f"[{key}: {vals[key]}]" for key in vals])
        
        new_record = None
        try:
            new_record = super(SmoDeviceAc, self).create(vals)
            _logger.info(f"Update DB [{crr_username}]: Create new AC record of device [{new_record.device_name}]: {changing_message} ➜ SUCCESS")
        except Exception as err:
            _logger.error(f"Update DB [{crr_username}]: Create new AC record: {changing_message} ➜ FAILED. Message: {err}")
            raise
        
        return new_record
    def write(self, vals):
        crr_username = self.env.user.name
        changing_message = ', '.join([f"[{key}: {self[key]} ➜ {vals[key]}]" for key in vals])
        ac_to_write = ', '.join([f"[{ac.device_name}]" for ac in self])
        
        result = None
        try:
            result = super(SmoDeviceAc, self).write(vals)
            _logger.info(f"Update DB [{crr_username}]: Update AC record of device {ac_to_write}: {changing_message} ➜ SUCCESS")
        except Exception as err:
            _logger.error(f"Update DB [{crr_username}]: Update AC record of device {ac_to_write}: {changing_message} ➜ FAILED. Message: {err}")
            raise
        
        skip_calling_api = self.env.context.get('skip_calling_api') or False
        keys_to_check = self._get_keys_to_fields_mapping().values()
        
        if not skip_calling_api and any(key in vals for key in keys_to_check):
            self.post_AC_status_to_server(vals)
            
        self._send_update_message()
        
        return result
    
    def _send_update_message(self):
        bus = self.env['bus.bus']
        for record in self:
            bus._sendone('smo_channel', 'smo.device.ac/update', {
                'id': record.id,
                'power_state': record.power_state,
                'temperature': record.temperature,
                'mode': record.mode,
                'fan_speed': record.fan_speed
            })
    
    def post_AC_status_to_server(self, vals):
        crr_username = self.env.user.name
        
        device_ids = {(ac.device_id, ac.device_name) for ac in self}
        
        tokens = self.env['smo.token'].get_tokens_of_id()
        if not tokens:
            _logger.error(f"Call API [{crr_username}]: POST data of AC devices to Thingsboards Server ➜ FAILED. Message: Token record not found")
            raise UserError('Token record not found')
            
        fields = {value: key for key, value in self._get_keys_to_fields_mapping().items()}
        
        payload = {
            'ss_' + fields[key]: int(vals[key]) if key in ['mode', 'fan_speed'] else vals[key]
            for key in fields.keys() & vals.keys()
        }
        
        for device_id in device_ids:
            endpoint = f'/api/plugins/telemetry/{device_id[0]}/SHARED_SCOPE'
            
            try:
                response = make_request(self, endpoint, method='POST', access_token=tokens.access_token, payload=payload)
                _logger.info(f'Call API [{crr_username}]: POST data of AC device [{device_id[1]}]: POST {endpoint}, payload: {payload} ➜ SUCCESS')
                response.raise_for_status()
            except requests.HTTPError as http_err:
                _logger.error(f'API Response [{crr_username}]: {response.status_code} - POST data of device [{device_id[1]}]: POST {endpoint}, payload: {payload} ➜ FAILED. Message: {json.loads(response.text)["message"]}')
                if response.status_code == 401:
                    self.env['smo.token'].refresh_access_token()
                    self.post_AC_status_to_server(vals)
                else:
                    raise UserError(f"Failed to call API to send AC device state: {response.text}")
            except Exception as err:
                _logger.error(f'Call API [{crr_username}]: POST data of AC device [{device_id[1]}]: POST {endpoint}, [payload: {payload}] ➜ FAILED. Message: {err}')
                raise UserError(f'Something went wrong! Please check your API URL and try again!')
            else:
                _logger.info(f'API Response [{crr_username}]: {response.status_code} - POST data of device [{device_id[1]}]: POST {endpoint}, payload: {payload} ➜ SUCCESS')
    
    def unlink(self):
        crr_username = self.env.user.name
        ac_to_delete = ', '.join([f"[{ac.device_name}]" for ac in self])
        
        result = None
        try:
            result = super(SmoDeviceAc, self).unlink()
            _logger.info(f"Update DB [{crr_username}]: Delete AC record of device {ac_to_delete} ➜ SUCCESS")
        except Exception as err:
            _logger.error(f"Update DB [{crr_username}]: Delete AC record of device [{ac_to_delete}] ➜ FAILED. Message: {err}")
            raise
        
        return result