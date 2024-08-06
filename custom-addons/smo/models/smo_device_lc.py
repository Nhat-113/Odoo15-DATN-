from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.http import request
from helper.smo_helper import make_request
import requests

class SmoDeviceLc(models.Model):
  _name = "smo.device.lc"
  _description = "SmartOffice LC Devices"
  _order = 'param_name asc'

  smo_device_id = fields.Many2one('smo.device', string="SmartOffice Device ID", required=True, ondelete='cascade')
  asset_control_id = fields.Char(string="Asset Control ID", required=True)
  asset_name = fields.Char(string="Asset Name", related="smo_device_id.asset_name")
  device_id = fields.Char(string="Device ID", required=True)
  device_name = fields.Char(string="Device Name")
  device_type= fields.Char(string="Device Type")
  param_name = fields.Char(string="Bulb", required=True)
  current_state = fields.Boolean(string="On/Off", required=True)
  _rec_name = "param_name"

  def write(self, vals):
    for record in self:
      if record.id and 'current_state' in vals:
        new_state = vals['current_state']
        if record.current_state != new_state:
          try:
            self.change_light_state(record.device_id, record.param_name, new_state)
          except Exception as err:
            raise UserError(f'Failed to change light state!')
    return super(SmoDeviceLc, self).write(vals)

  def change_light_state(self, device_id, key, state, smo_uid=None, update_local=False):
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
      response = make_request(self, endpoint, method='POST',
                    payload=payload,
                    access_token=tokens.access_token)
      response.raise_for_status()

      if update_local == True:
        record = self.search([('device_id', '=', device_id), ('param_name', '=', key)])
        if record:
          record.write({'current_state': state})
          self.env.cr.commit()
    except requests.HTTPError as http_err:
      if response.status_code == 401:
        self.env['smo.token'].refresh_access_token(smo_uid)
        self.change_light_state(device_id, key, state, smo_uid)
      else:
        raise UserError(f"Failed to call API to change light state: {response.text}")
    except Exception as err:
      raise UserError(f'Something went wrong! Please check your API URL and try again!')
