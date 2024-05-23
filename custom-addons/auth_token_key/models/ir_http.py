# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from werkzeug.exceptions import BadRequest

from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _auth_method_bearer_token(cls):
        try:
            access_token = request.httprequest.headers.get('Authorization')
            if not access_token:
                raise BadRequest('Access Token missing')

            if access_token.startswith('Bearer '):
                access_token = access_token[7:]
            request.uid = 1
            auth_api_token = request.env["auth.api.token"]._retrieve_api_key(access_token)
            if auth_api_token:
                request._env = None
                request.uid = auth_api_token.user_id.id
                request.auth_api_token = access_token
                request.auth_api_token_id = auth_api_token.id
                return True
        except:
            raise AccessDenied()


    

       
