from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.http import request
from helper.smo_helper import make_request
import requests
import json
import logging

_logger = logging.getLogger('smo.logger')
    
class SmoDeviceLc(models.Model):
    _name = "smo.device.lc"
    _description = "SmartOffice LC Devices"
    _order = 'name asc'

    name = fields.Char(string="Bulb", default=lambda lc: lc.param_name)
    
    smo_device_id = fields.Many2one('smo.device', string="SmartOffice Device ID", required=True, ondelete='cascade')
    device_id = fields.Char(string="Device ID", required=True)
    device_name = fields.Char(string="Device Name")
    device_type= fields.Char(string="Device Type")
    
    asset_control_id = fields.Char(string="Asset Control ID", required=True)
    asset_name = fields.Char(string="Asset Name", related="smo_device_id.asset_name")
    
    param_name = fields.Char(string="Light Code", required=True)
    current_state = fields.Boolean(string="On/Off", required=True)

    def write(self, vals):
        skip_calling_api = self.env.context.get('skip_calling_api') or False
                
        for record in self:
            if record.id and 'current_state' in vals:
                new_state = vals['current_state']
                try:
                    if not skip_calling_api:
                        self.change_light_state(record.device_id, record.param_name, new_state)
                    self._send_update_message(record.id, new_state)
                except Exception as err:
                    raise UserError(f'Failed to change light state!')
        return super(SmoDeviceLc, self).write(vals)

    def change_light_state(self, device_id, key, state, smo_uid=None):
        if not smo_uid:
            smo_user_record = self.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id if smo_user_record else self.env['smo.user'].login()

        endpoint = f'/api/plugins/telemetry/{device_id}/SHARED_SCOPE'
        post_key = 'ss_' + key
        payload = { post_key: state }
        tokens = self.env['smo.token'].get_tokens_of_id(smo_uid)
        
        if not tokens:
            raise UserError('Token record not found.')

        try:
            _logger.info(f'Call API to update light state of {key} of device: {device_id} - payload: {payload}')
            response = make_request(self, endpoint, method='POST',
                            payload=payload,
                            access_token=tokens.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to update light state of {key} of device: {device_id} failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                self.change_light_state(device_id, key, state, smo_uid)
            else:
                raise UserError(f"Failed to call API to change light state: {response.text}")
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to update light state of {key} failed: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')
        else:
            _logger.info(f'API Server Response: {response.status_code} - Call API to update light state of {key} of device: {device_id}  successfully')

    def _send_update_message(self, record_id, new_state):
        self.env['bus.bus']._sendone('smo_channel', 'smo.device.lc/update', {
            'id': record_id,
            'current_state': new_state
        })
