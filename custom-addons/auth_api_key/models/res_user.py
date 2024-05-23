from odoo import models

class ResUserRemove(models.Model):
    _inherit = 'res.users'

    def unlink(self):
    
        auth_api_key = self.env['auth.api.key'].sudo().search([("user_id", "in", self.ids)])
    
        if auth_api_key:
            auth_api_key.sudo().unlink()
            
        return super().unlink()
