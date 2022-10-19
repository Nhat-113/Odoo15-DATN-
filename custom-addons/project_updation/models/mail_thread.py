from odoo import models
from werkzeug import urls


class MailThreadCustom(models.AbstractModel):
    _inherit = 'mail.thread'

    def _notify_get_action_link_custom_mtech(self, link_type, action_id, project_id, view_type, **kwargs):
        """ Prepare link to an action: view document, follow document, ... """
        params = {
            'action': action_id,
            'active_id': project_id,
            'model': kwargs.get('model', self._name),
            'view_type': view_type,
        }
        # whitelist accepted parameters: action (deprecated), token (assign), access_token
        # (view), auth_signup_token and auth_login (for auth_signup support)
        params.update(dict(
            (key, value)
            for key, value in kwargs.items()
            if key in ('action', 'token', 'access_token', 'auth_signup_token', 'auth_login')
        ))

        if link_type in ['view', 'assign', 'follow', 'unfollow']:
            base_link = '/web#'
        elif link_type == 'controller':
            controller = kwargs.get('controller')
            params.pop('model')
            base_link = '%s' % controller
        else:
            return ''

        if link_type not in ['view']:
            token = self._notify_encode_link(base_link, params)
            params['token'] = token

        link = '%s%s' % (base_link, urls.url_encode(params))
        if self:
            link = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')]).value + link

        return link