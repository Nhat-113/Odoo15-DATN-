from odoo import models, api


class ResUsers(models.Model):
    _inherit = "res.users"
    
    @api.constrains('active')
    def _remove_api_token(self):
        for record in self:
            auth_api_token = self.env['auth.api.token'].sudo().search([("user_id", "=", record.id)])
            if auth_api_token:
                if record.active == False:
                    auth_api_token.sudo().unlink()