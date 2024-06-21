from odoo import models, fields, api
from odoo.http import request
from helper.smo_helper import make_request
from odoo.exceptions import UserError
from datetime import datetime
import requests
import json

class SmoDevice(models.Model):
  _name = "smo.device"
  _description = "SmartOffice Devices"

  smo_asset_id = fields.Many2one('smo.asset', string="SmartOffice Asset ID", required=True, ondelete='cascade')
  asset_id = fields.Char(string='Asset ID')
  asset_name = fields.Char(string='Asset Name')
  device_id = fields.Char(string="Device ID", required=True)
  device_name = fields.Char(string="Device Name", required=True)
  device_type = fields.Char(string="Device Type", required=True)
  smo_device_iaq_ids = fields.One2many('smo.device.iaq', 'smo_device_id', string='IAQ Device Records')
  smo_device_lc_ids = fields.One2many('smo.device.lc', 'smo_device_id', string='LC Device Records')
  last_sync_time =fields.Datetime(string='Last Sync Time', required=True)
  _rec_name = "device_name"

  @api.model
  def fetch_devices(self, smo_uid):
    assets_id = self.env['smo.asset'].fetch_assets(smo_uid)
    if not assets_id:
      raise UserError('An error occurred while fetching assets.')

    tokens = self.env['smo.token'].get_tokens_of_id(smo_uid)
    if not tokens:
      raise UserError('Token record not found.')

    fetched_devices = []
    for asset_id in assets_id:
      params = {'fromId': asset_id, 'fromType': 'ASSET'}
    
      try:
        response = make_request('/api/relations/info', method='GET',
                  params=params,
                  access_token=tokens.access_token)
        response.raise_for_status()
      except requests.HTTPError as http_err:
        if response.status_code == 401:
          self.env['smo.token'].refresh_access_token(smo_uid)
          self.fetch_devices(smo_uid)
        else:
          raise UserError(f'Failed to fetch devices: {response.text}')
      except Exception as err:
        raise UserError(f'An error occurred: {str(err)}')

      asset_record = self.env['smo.asset'].search([('asset_id', '=', asset_id)], limit=1)
      if not asset_record:
        raise UserError('Asset record not found')
        
      existing_devices = {device.device_id: device for device in self.search([('smo_asset_id', '=', asset_record.id)])}

      data = response.json()
      for device in data:
        device_id = device['to']['id']
        device_name = device['toName']
        device_type = device['additionalInfo']['deviceType']

        smo_device_id = -1
        if device_id in existing_devices:
          existing_devices[device_id].write({
            'asset_id': asset_record.asset_id,
            'asset_name': asset_record.asset_name,
            'device_name': device_name,
            'device_type': device_type,
            'last_sync_time': fields.Datetime.now()
          })
          smo_device_id = existing_devices[device_id].id
        else:
          new_device_record = self.create({
            'smo_asset_id': asset_record.id,
            'asset_id': asset_record.asset_id,
            'asset_name': asset_record.asset_name,
            'device_id': device_id,
            'device_name': device_name,
            'device_type': device_type,
            'last_sync_time': fields.Datetime.now()
          })
          smo_device_id = new_device_record.id
          
        device_info = {
          'id':  smo_device_id,
          'device_id': device_id,
          'type': device_type
        }
        if device_type == 'LC':
          device_info.update({'Asset': device['additionalInfo']['Asset']})

        fetched_devices.append(device_info)
  
      devices_to_delete = [device for device_id, device in existing_devices.items() if device_id not in [d['device_id'] for d in fetched_devices]]
      for device in devices_to_delete:
        device.unlink()

      self.env.cr.commit()

    return fetched_devices

  @api.model
  def fetch_devices_detail(self, smo_uid=None, reload=True):
    if not smo_uid:
      smo_user_record = self.env['smo.user'].search([], limit=1)
      smo_uid = smo_user_record.id if smo_user_record else self.env['smo.user'].login()

    devices = self.fetch_devices(smo_uid)
    if not devices:
      raise UserError('An error occurred while fetching devices.')

    tokens_record = self.env['smo.token'].get_tokens_of_id(smo_uid)
    if not tokens_record:
      raise UserError('Token record not found.')

    for device in devices:
      smo_device_record = self.search([('id', '=', device['id'])], limit=1)        
      if not smo_device_record:
        continue
      
      if device['type'] == 'IAQ':
        self.fetch_iaq_devices(device, smo_device_record, tokens_record, smo_uid)
      elif device['type'] == 'LC':
        self.fetch_lc_devices(device, smo_device_record, tokens_record, smo_uid)
      else:
        # Other device types are not supported
        pass

    self.env.cr.commit()

    if reload == True:
      return {
      'type': 'ir.actions.client',
      'tag': 'reload',
      }

  @api.model
  def fetch_iaq_devices(self, device, smo_device_record, tokens_record, smo_uid):
    device_id = device['device_id']
    smo_device_id = smo_device_record.id

    params = {'useStrictDataTypes': False}
    endpoint = f'/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries'

    try:
      response = make_request(endpoint, method='GET',
                params=params,
                access_token=tokens_record.access_token)
      response.raise_for_status()
    except requests.HTTPError as http_err:
      if response.status_code == 401:
        self.env['smo.token'].refresh_access_token(smo_uid)
        self.fetch_devices_detail(smo_uid=smo_uid)
      else:
        raise UserError(f'Failed to fetch IAQ device data: {response.text}')
    except Exception as err:
      raise UserError(f'An error occurred: {str(err)}')

    iaq_model = self.env['smo.device.iaq']
    existing_iaq_records = {rec.param_name: rec for rec in iaq_model.search([('smo_device_id', '=', smo_device_id)])}

    data = response.json()
    for parameter in data:
      current_value = data[parameter][0]['value']
      last_updated = datetime.fromtimestamp(data[parameter][0]['ts'] / 1000)
      if parameter in existing_iaq_records:
        existing_iaq_records[parameter].write({
          'current_value': current_value,
          'last_updated': last_updated
        })
      else:
        iaq_model.create({
          'smo_device_id': smo_device_id,
          'device_id': device_id,
          'device_name': smo_device_record.device_name,
          'device_type': smo_device_record.device_type,
          'param_name': parameter,
          'current_value': current_value,
          'last_updated': last_updated
        })

    for param_name in set(existing_iaq_records) - set(data):
      existing_iaq_records[param_name].unlink()

  @api.model
  def fetch_lc_devices(self, device, smo_device_record, tokens_record, smo_uid):
    device_id = device['device_id']
    smo_device_id = smo_device_record.id

    endpoint = f'/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/CLIENT_SCOPE'
        
    try:
      response = make_request(endpoint, method='GET', access_token=tokens_record.access_token)
      response.raise_for_status()
    except requests.HTTPError as http_err:
      if response.status_code == 401:
        self.env['smo.token'].refresh_access_token(smo_uid)
        self.fetch_devices_detail(smo_uid=smo_uid)
      else:
        raise UserError(f'Failed to fetch LC device data: {response.text}')
    except Exception as err:
      raise UserError(f'An error occurred: {str(err)}')

    lc_model = self.env['smo.device.lc']
    existing_lc_records = {(rec.param_name, rec.asset_control_id): rec for rec in lc_model.search([('smo_device_id', '=', smo_device_id)])}

    list_controlled_asset = self.filter_controlled_assets(smo_uid, device['Asset'])
    
    data = response.json()
    new_keys = set()
    for item in data:
      for asset_id in list_controlled_asset:
        if item['key'] in list_controlled_asset[asset_id] and smo_device_record.asset_id == asset_id:
          current_state = item['value']
          key = (item['key'], asset_id)
          new_keys.add(key)
          if key in existing_lc_records:
            existing_lc_records[key].write({
              'current_state': current_state
            })
          else:
            lc_model.create({
              'smo_device_id': smo_device_id,
              'asset_control_id': asset_id,
              'device_id': device_id,
              'device_name': smo_device_record.device_name,
              'device_type': smo_device_record.device_type,
              'param_name': item['key'],
              'current_state': current_state
            })

    old_keys = set(existing_lc_records)
    keys_to_remove = old_keys - new_keys
    for key in keys_to_remove:
        existing_lc_records[key].unlink()

  @api.model
  def filter_controlled_assets(self, smo_uid, dict_assets_LC):
    tenant_record = self.env['smo.tenant'].search([('smo_user_id', '=', smo_uid)], limit=1)
    if not tenant_record:
      raise Exception('Tenant record not found.')
    
    assets_records = self.env['smo.asset'].search([('smo_tenant_id', '=', tenant_record.id)])
    if not assets_records:
      raise Exception('Asset record not found.')
    
    list_assets_in_record = [asset.asset_id for asset in assets_records]
    common_keys = set(dict_assets_LC.keys() & set(list_assets_in_record))
    return {key: dict_assets_LC[key] for key in common_keys}

  @api.model
  def sync_all(self):
    smo_users_record = self.env['smo.user'].search([])
    for record in smo_users_record:
      smo_uid = record.id
      self.fetch_devices_detail(smo_uid, reload=False)
      
    return {
      'type': 'ir.actions.client',
      'tag': 'reload',
    }
