from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger('smo.logger')

class SocketController(http.Controller):

    @http.route('/smo/socket/init', type='json', auth='user')
    def get_init_data(self):
        try:
            ir_config = request.env['ir.config_parameter'].sudo()
            socket_active = ir_config.get_param('smo.auto_sync_socket') or False
            
            if not socket_active:
                return {
                    'status': 200,
                    'message': 'Auto Sync: WebSocket is not active',
                    'data': {
                        'socket_active': False
                    }
                }
                    
            realtime_sync_devices = request.env['smo.device'].search_read(
                [('device_type', 'in', ['LC', 'AC'])],
                ['id', 'device_id']
            )
            device_to_subscribe = [{'id': device['id'], 'device_id': device['device_id']} for device in realtime_sync_devices]
        
            smo_user_record = request.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id if smo_user_record else request.env['smo.user'].login()
            
            tokens = request.env['smo.token'].get_tokens_of_id(smo_uid)
            
            ir_config = request.env['ir.config_parameter'].sudo()
            wss_url = ir_config.get_param('smo.thingsboard_wss_url')
            
            return {
                'status': 200,
                'data': {
                    'socket_active': True,
                    'wss_url': wss_url,
                    'token': tokens.access_token,
                    'devices': device_to_subscribe   
                }
            }
        except Exception as e:
            _logger.error(f"Odoo Server Error: Error while fetching init data for Socket connection: {str(e)}")
            return {'status': 500, 'message': str(e)}
        
    @http.route('/smo/socket/device', type='json', auth='user', methods=['POST'])
    def process_lc_data(self, **kw):
        try:
            message = json.loads(kw['message']) if kw['message'] else None
            if not message:
                return {'status': 200, 'message': 'Empty message'}
            
            _logger.info(f'Receive Socket message: {message}')
            
            smo_device_id = message.get('subscriptionId')
            if not smo_device_id:
                return {'status': 400, 'message': 'Missing subscriptionId'}
            
            subscribed_device = request.env['smo.device'].browse(smo_device_id)
            if not subscribed_device:
                return {'status': 404, 'message': 'No matching devices found'}
            
            if subscribed_device.device_type == 'LC':
                lc_devices = subscribed_device.smo_device_lc_ids
                param_names = {lc.param_name for lc in lc_devices}
                filtered_data = {key: json.loads(data[0][1]) for key, data in message['data'].items() if key in param_names}

                _logger.info(f'Parsed LC data received from WebSocket: {filtered_data}')
                
                for lc in lc_devices:
                    new_state = filtered_data.get(lc.param_name)
                    if new_state is not None and lc.current_state != new_state:
                        _logger.info(f"Update DB: (from Socket) Update LC record of {lc.param_name}-{lc.name or lc.param_name} of device [{lc.device_name}]: [state: {lc.current_state} ➜ {new_state}]")
                        lc.with_context(skip_calling_api=True).write({'current_state': new_state})
            
            elif subscribed_device.device_type == 'AC':
                ac_device = subscribed_device.smo_device_ac_ids
                keys_to_fields = ac_device._get_keys_to_fields_mapping()
                
                def process_ac_value(key, value):
                    if key in ['powerState']:
                        return value.lower() == 'true'
                    if key in ['temp']:
                        return int(value)
                    return value
                
                filtered_data = {keys_to_fields[key]: process_ac_value(key, data[0][1]) for key, data in message['data'].items() if key in keys_to_fields}
                
                _logger.info(f'Parsed AC data received from WebSocket: {filtered_data}')
                
                ac_device.with_context(skip_calling_api=True).write(filtered_data)


            return {'status': 200, 'message': 'Data processed successfully'}
        except Exception as e:
            _logger.error(f"Odoo Server Error: Error while processing data from Socket in Odoo API: {str(e)}")
            return {'status': 500, 'message': str(e)}
        
    @http.route('/smo/token/refresh', type='json', auth='user')
    def refresh_token(self):
        try:
            smo_user_record = request.env['smo.user'].search([], limit=1)
            smo_uid = smo_user_record.id if smo_user_record else request.env.user.id

            token_refreshed = request.env['smo.token'].refresh_access_token(smo_uid)

            if token_refreshed:
                return {'status': 200, 'message': 'Tokens refreshed successfully'}
            
            return {'status': 400, 'message': 'Failed to refresh tokens'}
        except Exception as e:
            _logger.error(f"Odoo Server Error: Error while refreshing tokens by API: {str(e)}")
            return {'status': 500, 'message': 'An error occurred while refreshing tokens'}
        
    @http.route('/smo/sync/manual', type='json', auth='user')
    def get_manual_sync_setting(self):
        try:
            ir_config = request.env['ir.config_parameter'].sudo()
            sync_manual = ir_config.get_param('smo.manual_sync') or False
            
            return {
                'status': 200,
                'data': {
                    'manual': sync_manual
                }
            }
        except Exception as e:
            _logger.error(f"Odoo Server Error: Error while getting sync manual setting by API: {str(e)}")
            return {'status': 500, 'message': 'An error occurred while getting sync manual setting'}
