from odoo import models

class ResUserRemove(models.Model):
    _inherit = 'res.users'

    def unlink(self):
        auth_api_token = self.env['auth.api.token'].sudo().search([("user_id", "in", self.ids)])
        if auth_api_token:
            auth_api_token.sudo().unlink()

        return super().unlink()
