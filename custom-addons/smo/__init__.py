from . import models

from odoo import api, SUPERUSER_ID

def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    ir_config = env['ir.config_parameter'].sudo()
    
    keys_to_unlink = [
        'smo.base_api_url',
        'smo.shared_account_username',
        'smo.shared_account_password',
        'smo.thingsboard_wss_url'
    ]

    ir_config.search([('key', 'in', keys_to_unlink)]).unlink()