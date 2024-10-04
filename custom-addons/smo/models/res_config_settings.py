from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    thingsboard_api_url = fields.Char(string="Thingsboard API URL",
        config_parameter='smo.base_api_url')
    thingsboard_shared_account_username = fields.Char(string="Username",
        config_parameter='smo.shared_account_username')
    thingsboard_shared_account_password = fields.Char(string="Password",
        config_parameter='smo.shared_account_password')
    thingsboard_wss_url = fields.Char(string="Thingsboard Websocket URL",
        config_parameter='smo.thingsboard_wss_url')
    smo_manual_sync = fields.Boolean(string="Manual Sync",
        config_parameter='smo.manual_sync', default=True)
    smo_auto_sync_socket = fields.Boolean(string="Auto Sync: WebSocket",
        config_parameter='smo.auto_sync_socket', default=True)
    smo_auto_sync_http = fields.Boolean(string="Auto Sync: HTTP",
        config_parameter='smo.auto_sync_http', default=True)
    dashboard_wiget = fields.Char(string="Dashboard Wiget URL",
        config_parameter='smo.dashboard_wiget')

    @api.onchange('thingsboard_api_url')
    def _onchange_thingsboard_api_url(self):
        if self.thingsboard_api_url:
            self.thingsboard_api_url = self.thingsboard_api_url.strip().strip('/')
            
            if not self.thingsboard_api_url.startswith(('http://', 'https://')):
                raise ValidationError("The Thingsboard API URL must be in the format 'http://example' or 'https://example'")
            
    @api.onchange('thingsboard_wss_url')
    def _onchange_thingsboard_wss_url(self):
        if self.thingsboard_wss_url:
            self.thingsboard_wss_url = self.thingsboard_wss_url.strip().strip('/')
            
            if not self.thingsboard_wss_url.startswith(('ws://', 'wss://')):
                raise ValidationError("The Thingsboard Websocket URL must be in the format 'ws://example' or 'wss://example'")

    @api.onchange('dashboard_wiget')
    def _onchange_dashboard_wiget(self):
        if self.dashboard_wiget:
            self.dashboard_wiget = self.dashboard_wiget.strip().strip('/')
            
            if not self.dashboard_wiget.startswith(('http://dev-dboard.d-soft.tech/', 'https://dev-dboard.d-soft.tech/')):
                raise ValidationError("The Dashboard Wiget URL must be in the format 'http://example' or 'https://example'")

    @api.onchange('thingsboard_shared_account_username')
    def _onchange_shared_account_username(self):
        if self.thingsboard_shared_account_username:
            self.thingsboard_shared_account_username = self.thingsboard_shared_account_username.strip()
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()

        field_config_param_map = [
            ('thingsboard_api_url', 'smo.base_api_url'),
            ('thingsboard_shared_account_username', 'smo.shared_account_username'),
            ('thingsboard_shared_account_password', 'smo.shared_account_password'),
            ('thingsboard_wss_url', 'smo.thingsboard_wss_url'),
            ('smo_manual_sync', 'smo.manual_sync'),
            ('smo_auto_sync_socket', 'smo.auto_sync_socket'),
            ('smo_auto_sync_http', 'smo.auto_sync_http'),
            ('dashboard_wiget', 'smo.dashboard_wiget'),
        ]

        for field, config_param in field_config_param_map:
            res[field] = ir_config.get_param(config_param)

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter']
        
        field_config_param_map = [
            ('thingsboard_api_url', 'smo.base_api_url'),
            ("thingsboard_shared_account_username", "smo.shared_account_username"),
            ("thingsboard_shared_account_password", "smo.shared_account_password"),
            ('thingsboard_wss_url', 'smo.thingsboard_wss_url'),
            ('smo_manual_sync', 'smo.manual_sync'),
            ('smo_auto_sync_socket', 'smo.auto_sync_socket'),
            ('smo_auto_sync_http', 'smo.auto_sync_http')
        ]

        for field, config_param in field_config_param_map:
            if self[field] != ir_config.get_param(config_param):
                ir_config.set_param(config_param, self[field])
