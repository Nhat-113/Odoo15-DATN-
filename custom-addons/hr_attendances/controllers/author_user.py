# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request, JsonRequest, Response
from werkzeug.wrappers import Response
from helper.helper import alternative_json_response, jsonResponse

import logging

_logger = logging.getLogger(__name__)


class AuthorUser(http.Controller):

    @http.route("/api/login", type="json", auth="public", methods=['POST'])
    def login(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            email = kw["email"]
            password = kw["password"]
            log_data = {
                'POST': '/api/login',
                'email': email,
            }
            uid = request.session.authenticate(request.session.db, email, password)
            if uid:
                key = request.env["auth.api.token"]._compute_default_key()
                check_key_exist = request.env["auth.api.token"].sudo().search([("user_id","=", uid)])
                if check_key_exist: 
                        check_key_exist.sudo().write({
                            "key": key,
                        })
                else:
                    request.env["auth.api.token"].sudo().create({
                            "key": key,
                            "user_id": uid
                        })
                employee_id = request.env.user.employee_id
                is_employee = bool(employee_id)
                res = {
                    "status": 200,
                    "is_employee": is_employee,
                }
                _logger.info({**log_data, **res})
                return {**res, **{"token": key}}
        except Exception as e:
            res = {"status": 401, "message": f"login failed: {e}"}
            _logger.info({**log_data, **res})
            return res

    @http.route("/api/logout", type="http", auth="bearer_token", methods=['POST'], csrf=False)
    def logout(self):
        try:
            if request.uid:
                log_data = {'POST': '/api/logout'}
                check_api_token = request.env["auth.api.token"].search([('user_id', '=', request.uid)])
                if check_api_token:
                    request.session.logout(keep_db=True)
                    check_api_token.sudo().unlink()

                    res = {"status": 200, "message": "Logout successfully"}
                    _logger.info({**log_data, **res})
                    return jsonResponse(res, 200 )
        except Exception as e:
            res = { "status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
