from . import models
from . import controllers

from odoo import api, SUPERUSER_ID

def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_config = env['ir.config_parameter'].sudo()
    
    ir_config.set_param('smo.manual_sync', True)
    ir_config.set_param('smo.auto_sync_socket', True)
    ir_config.set_param('smo.auto_sync_http', True)
    
def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_config = env['ir.config_parameter'].sudo()
    
    keys_to_unlink = [
        'smo.base_api_url',
        'smo.shared_account_username',
        'smo.shared_account_password',
        'smo.thingsboard_wss_url',
        'smo.manual_sync',
        'smo.auto_sync_socket',
        'smo.auto_sync_http'
    ]

    ir_config.search([('key', 'in', keys_to_unlink)]).unlink()
    
    device_lc_schedule = env['smo.device.lc.schedule']
    
    schedules = device_lc_schedule.search([])
    if schedules:
        schedules.unlink()