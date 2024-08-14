from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

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
                    
            lc_devices = request.env['smo.device'].search_read(
                [('device_type', '=', 'LC')],
                ['id', 'device_id']
            )
            device_to_subscribe = [{'id': device['id'], 'device_id': device['device_id']} for device in lc_devices]
        
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
            _logger.error(f"Error fetching init data: {str(e)}")
            return {'status': 500, 'message': str(e)}
        
    @http.route('/smo/socket/device/lc', type='json', auth='user', methods=['POST'])
    def process_lc_data(self, **kw):
        try:
            message = json.loads(kw['message']) if kw['message'] else None
            
            if not message:
                return {'status': 200, 'message': 'Empty message'}
            
            smo_device_id = message.get('subscriptionId')
            if not smo_device_id:
                return {'status': 400, 'message': 'Missing subscriptionId'}
            
            lc_devices = request.env['smo.device.lc'].search([('smo_device_id', '=', smo_device_id)])
            
            if not lc_devices:
                _logger.warning("No devices found for subscription ID %s", smo_device_id)
                return {'status': 404, 'message': 'No matching devices found'}
            
            param_names = {lc.param_name for lc in lc_devices}
            filtered_data = {key: json.loads(data[0][1]) for key, data in message['data'].items() if key in param_names}

            for lc in lc_devices:
                new_state = filtered_data.get(lc.param_name)
                if new_state is not None and lc.current_state != new_state:
                    lc.with_context(skip_calling_api=True).write({'current_state': new_state})
                
            return {'status': 200, 'message': 'Data processed successfully'}
        except Exception as e:
            _logger.error(f"Error processing LC data: {str(e)}")
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
            _logger.exception("Error refreshing tokens: %s", e)
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
            _logger.exception("Error refreshing tokens: %s", e)
            return {'status': 500, 'message': 'An error occurred while refreshing tokens'}
