from odoo import models, fields, api
from odoo.http import request
from helper.smo_helper import make_request
from odoo.exceptions import UserError
from datetime import datetime
import requests
import json
import logging

_logger = logging.getLogger('smo.logger')

NON_IAQ_LIST = {
    'current_fw_version',
    'current_fw_title',
    'current_fw_state',
    'fw_state',
    'ipAddress',
    'macAddress',
    'rssi',
    'target_fw_version',
    'target_fw_title',
    'target_fw_tag',
    'target_fw_ts',
    'otaPermission',
}

class SmoDevice(models.Model):
    _name = "smo.device"
    _description = "SmartOffice Devices"
    _rec_name = "device_name"
    
    smo_asset_id = fields.Many2one('smo.asset', string="SmartOffice Asset ID", required=True, ondelete='cascade')
    asset_id = fields.Char(string='Asset ID')
    asset_name = fields.Char(string='Asset Name')
    
    device_id = fields.Char(string="Device ID", required=True)
    device_name = fields.Char(string="Device Name", required=True)
    device_type = fields.Char(string="Device Type", required=True)
    
    smo_device_iaq_ids = fields.One2many('smo.device.iaq', 'smo_device_id', string='IAQ Device Records')
    smo_device_lc_ids = fields.One2many('smo.device.lc', 'smo_device_id', string='LC Device Records')
    smo_device_ac_ids = fields.One2many('smo.device.ac', 'smo_device_id', string='AC Device Records')
    
    last_sync_time =fields.Datetime(string='Last Sync Time', required=True)

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
                _logger.info(f'Call API to fetch devices data of asset id: {asset_id}')
                response = make_request(self, '/api/relations/info', method='GET',
                                params=params,
                                access_token=tokens.access_token)
                response.raise_for_status()
            except requests.HTTPError as http_err:
                _logger.error(f'API Server Response: {response.status_code} - Call API to fetch devices of asset id: {asset_id} failed: {json.loads(response.text)["message"]}')
                if response.status_code == 401:
                    self.env['smo.token'].refresh_access_token(smo_uid)
                    self.fetch_devices(smo_uid)
                else:
                    raise UserError(f'Failed to fetch devices: {response.text}')
            except Exception as err:
                _logger.error(f'Odoo Server Error: Call API to fetch devices data of asset id: {asset_id}: {err}')
                raise UserError(f'Something went wrong! Please check your API URL and try again!')

            try:
                _logger.info(f'API Server Response: {response.status_code} - Call API to fetch devices of asset id: {asset_id} successfully')
                _logger.info(f'Parse response data of devices')
                data = response.json()
            except Exception as err:
                _logger.error('Odoo Server Error: Failed to parse response data of devices')
                raise UserError('Failed to parse response data of devices')

            asset_record = self.env['smo.asset'].search([('asset_id', '=', asset_id)], limit=1)
            if not asset_record:
                raise UserError('Asset record not found')

            existing_devices = {device.device_id: device for device in self.search([('smo_asset_id', '=', asset_record.id)])}

            for device in data:
                device_id = device['to']['id']
                device_name = device['toName']
                device_type = device['additionalInfo']['deviceType']

                smo_device_id = -1
                if device_id in existing_devices:
                    _logger.info(f'Update DB: Update device [{existing_devices[device_id].device_name}] info')
                    existing_devices[device_id].write({
                        'asset_id': asset_record.asset_id,
                        'asset_name': asset_record.asset_name,
                        'device_name': device_name,
                        'device_type': device_type,
                        'last_sync_time': fields.Datetime.now()
                    })
                    smo_device_id = existing_devices[device_id].id
                else:
                    _logger.info(f'Update DB: Create new device record to store data of device [{device_name}]')
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
                _logger.info(f'Update DB: Delete device record [{device.device_name}]')
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
                self.fetch_iaq_devices(smo_device_record, tokens_record, smo_uid)
            elif device['type'] == 'LC':
                self.fetch_lc_devices(smo_device_record, tokens_record, smo_uid, device['Asset'])
            elif device['type'] == 'AC':
                self.fetch_ac_devices(smo_device_record, tokens_record, smo_uid)
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
    def fetch_iaq_devices(self, smo_device_record, tokens_record, smo_uid):
        smo_device_id = smo_device_record.id
        device_id = smo_device_record.device_id

        params = {'useStrictDataTypes': False}
        endpoint = f'/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries'

        try:
            _logger.info(f'Call API to fetch IAQ device data of device [{smo_device_record.device_name}]')
            response = make_request(self, endpoint, method='GET',
                            params=params,
                            access_token=tokens_record.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to fetch IAQ device data of device [{smo_device_record.device_name}] failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                self.fetch_devices_detail(smo_uid=smo_uid)
            else:
                raise UserError(f'Failed to fetch IAQ device data: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to fetch IAQ device data of device [{smo_device_record.device_name}]: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')

        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to fetch IAQ device data of device [{smo_device_record.device_name}] successfully')
            _logger.info(f'Parse response data of IAQ Sensor devices of device [{smo_device_record.device_name}]')
            data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse response data of IAQ devices of device [{smo_device_record.device_name}]: {err}')
            raise UserError('Failed to parse response data of IAQ Sensor devices')

        iaq_model = self.env['smo.device.iaq']
        existing_iaq_records = {rec.param_name: rec for rec in iaq_model.search([('smo_device_id', '=', smo_device_id)])}
        non_iaq_records = {}
        
        for parameter in data:
            if parameter in NON_IAQ_LIST:
                if parameter in existing_iaq_records:
                    non_iaq_records.update({parameter: existing_iaq_records[parameter]})
                continue
            
            current_value = data[parameter][0]['value']
            last_updated = datetime.fromtimestamp(data[parameter][0]['ts'] / 1000)
            if parameter in existing_iaq_records:
                _logger.info(f'Update DB: Update IAQ record of {parameter} index of device [{existing_iaq_records[parameter].device_name}]: [value: {existing_iaq_records[parameter].current_value} ➜ {current_value}]')
                existing_iaq_records[parameter].write({
                    'current_value': current_value,
                    'last_updated': last_updated
                })
            else:
                _logger.info(f'Update DB: Create new IAQ record to store data of {parameter} index of device [{smo_device_record.device_name}]')
                iaq_model.create({
                    'smo_device_id': smo_device_id,
                    'device_id': device_id,
                    'device_name': smo_device_record.device_name,
                    'device_type': smo_device_record.device_type,
                    'param_name': parameter,
                    'current_value': current_value,
                    'last_updated': last_updated
                })

        _logger.info(f'Update DB: Update last sync time of device [{smo_device_record.device_name}]')
        smo_device_record.write({
            'last_sync_time': fields.Datetime.now()
        })

        parameters_to_remove = set(existing_iaq_records) - set(data)
        
        for param_name in set(existing_iaq_records):
            if param_name in parameters_to_remove or param_name in non_iaq_records:
                _logger.info(f'Update DB: Delete IAQ record of {param_name} index of device [{smo_device_record.device_name}]')
                existing_iaq_records[param_name].unlink()
        
        self.env.cr.commit()

    @api.model
    def fetch_lc_devices(self, smo_device_record, tokens_record, smo_uid, control_asset_list):
        smo_device_id = smo_device_record.id
        device_id = smo_device_record.device_id

        endpoint = f'/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/CLIENT_SCOPE'
            
        try:
            _logger.info(f'Call API to fetch LC device data of device [{smo_device_record.device_name}]')
            response = make_request(self, endpoint, method='GET', access_token=tokens_record.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to fetch LC device data of device [{smo_device_record.device_name}] failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                self.fetch_devices_detail(smo_uid=smo_uid)
            else:
                raise UserError(f'Failed to fetch LC device data: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to fetch LC device data of device [{smo_device_record.device_name}]: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')
        
        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to fetch LC device data of device [{smo_device_record.device_name}] successfully')
            _logger.info(f'Parse response data of LC devices of device [{smo_device_record.device_name}]')
            data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse response data of LC devices of device [{smo_device_record.device_name}]: {err}')
            raise UserError('Failed to parse response data of Light Control devices')

        lc_model = self.env['smo.device.lc']
        existing_lc_records = {(rec.param_name, rec.asset_control_id): rec for rec in lc_model.search([('smo_device_id', '=', smo_device_id)])}

        list_controlled_asset = self.filter_controlled_assets(smo_uid, control_asset_list)
        
        new_keys = set()
        for item in data:
            for asset_id in list_controlled_asset:
                if item['key'] in list_controlled_asset[asset_id] and smo_device_record.asset_id == asset_id:
                    current_state = item['value']
                    key = (item['key'], asset_id)
                    new_keys.add(key)
                    if key in existing_lc_records:
                        _logger.info(f'Update DB: Update LC record of {item["key"]}-{existing_lc_records[key].name or existing_lc_records[key].param_name} of device [{smo_device_record.device_name}]: [state: {existing_lc_records[key].current_state} ➜ {current_state}]')
                        existing_lc_records[key].with_context(skip_calling_api=True).write({
                            'current_state': current_state
                        })
                    else:
                        _logger.info(f'Update DB: Create new LC record to store data of {item["key"]} of device [{smo_device_record.device_name}]')
                        lc_model.create({
                            'smo_device_id': smo_device_id,
                            'asset_control_id': asset_id,
                            'device_id': device_id,
                            'device_name': smo_device_record.device_name,
                            'device_type': smo_device_record.device_type,
                            'param_name': item['key'],
                            'current_state': current_state
                        })

        _logger.info(f'Update DB: Update last sync time of device [{smo_device_record.device_name}]')
        smo_device_record.write({
            'last_sync_time': fields.Datetime.now()
        })

        old_keys = set(existing_lc_records)
        keys_to_remove = old_keys - new_keys
        for key in keys_to_remove:
            _logger.info(f'Update DB: Delete LC record of {key[0]}-{existing_lc_records[key].name or existing_lc_records[key].param_name} of device [{smo_device_record.device_name}]')
            existing_lc_records[key].unlink()

        self.env.cr.commit()
        
    @api.model
    def fetch_ac_devices(self, smo_device_record, tokens_record, smo_uid):
        smo_device_id = smo_device_record.id
        device_id = smo_device_record.device_id

        endpoint = f'/api/plugins/telemetry/DEVICE/{device_id}/values/attributes/CLIENT_SCOPE'
            
        try:
            _logger.info(f'Call API to fetch AC device data of device [{smo_device_record.device_name}]')
            response = make_request(self, endpoint, method='GET', access_token=tokens_record.access_token)
            response.raise_for_status()
        except requests.HTTPError as http_err:
            _logger.error(f'API Server Response: {response.status_code} - Call API to fetch AC device data of device [{smo_device_record.device_name}] failed: {json.loads(response.text)["message"]}')
            if response.status_code == 401:
                self.env['smo.token'].refresh_access_token(smo_uid)
                self.fetch_devices_detail(smo_uid=smo_uid)
            else:
                raise UserError(f'Failed to fetch AC device data: {response.text}')
        except Exception as err:
            _logger.error(f'Odoo Server Error: Call API to fetch AC device data of device [{smo_device_record.device_name}]: {err}')
            raise UserError(f'Something went wrong! Please check your API URL and try again!')
        
        try:
            _logger.info(f'API Server Response: {response.status_code} - Call API to fetch AC device data of device [{smo_device_record.device_name}] successfully')
            _logger.info(f'Parse response data of AC devices of device [{smo_device_record.device_name}]')
            data = response.json()
        except Exception as err:
            _logger.error(f'Odoo Server Error: Failed to parse response data of AC devices of device [{smo_device_record.device_name}]: {err}')
            raise UserError('Failed to parse response data of Air Conditioner devices')

        _logger.info(f'Raw AC Data: {data}')
        ac_model = self.env['smo.device.ac']
        existing_ac_records = ac_model.search([('smo_device_id', '=', smo_device_id)])
        
        if existing_ac_records:
            existing_ac_records.write({
                'temperature': 17,
                'mode': 'AUTO',
                'fan_speed': 'AUTO',
                'power_state': True
            })
        else:
            self.env['smo.device.ac'].create({
                'smo_device_id': smo_device_record.id,
                'temperature': 17,
                'mode': 'AUTO',
                'fan_speed': 'AUTO',
                'power_state': True
            })
            
        _logger.info(f'Update DB: Update last sync time of device [{smo_device_record.device_name}]')
        smo_device_record.write({
            'last_sync_time': fields.Datetime.now()
        })

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
    def cron_auto_sync_all(self):
        ir_config = self.env['ir.config_parameter'].sudo()
        http_auto_sync_active = ir_config.get_param('smo.auto_sync_http') or False
        
        if not http_auto_sync_active:
            return
        
        smo_users_record = self.env['smo.user'].search([])
        for record in smo_users_record:
            smo_uid = record.id
            self.fetch_devices_detail(smo_uid, reload=False)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def sync_single_device(self, smo_uid=None):
        if not smo_uid:
            smo_user_record = self.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id if smo_user_record else self.env['smo.user'].login()

        tokens_record = self.env['smo.token'].get_tokens_of_id(smo_uid)
        if not tokens_record:
            raise UserError('Token record not found.')

        for record in self:
            if record.device_type == 'IAQ':
                self.fetch_iaq_devices(record, tokens_record, smo_uid)
            elif record.device_type == 'LC':
                devices = self.fetch_devices(smo_uid)
                if not devices:
                    raise UserError('An error occurred while fetching devices.')

                control_asset_list = {}
                for device in devices:
                    if device['id'] == record.id:
                        control_asset_list = device.get('Asset', {})
                        break
                
                self.fetch_lc_devices(record, tokens_record, smo_uid, control_asset_list)
            else:
                # Other device types are not supported
                pass

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SmoDevice, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if toolbar:
            sync_manual = self.env['ir.config_parameter'].sudo().get_param('smo.manual_sync') or False

            if 'action' in res['toolbar'] and not sync_manual:
                sync_all_action_id = self.env.ref('smo.sync_data_action').id or -1
                sync_one_action_id = self.env.ref('smo.sync_data_action_specific_device').id or -1
                res['toolbar']['action'] = [action for action in res['toolbar']['action'] 
                                                if action['id'] not in [sync_all_action_id, sync_one_action_id]]
        
        return res
        

