from odoo import models, api


class ResUsers(models.Model):
    _inherit = "res.users"
    
    @api.constrains('active')
    def _remove_api_token(self):
        auth_api_token = self.env['auth.api.token'].search([('user_id', 'in', self.ids)])
        auth_api_key = self.env['auth.api.key'].search([('user_id', 'in', self.ids)])
        if auth_api_token or auth_api_key:
            for record in self:
                if record.active == False:
                    auth_api_token.unlink()
                    auth_api_key.unlink()