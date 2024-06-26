# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request, JsonRequest, Response
from werkzeug.wrappers import Response
from helper.helper import alternative_json_response, jsonResponse

class AuthorUser(http.Controller):

    @http.route("/api/login", type="json", auth="public", methods=['POST'])
    def login(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            email = kw["email"]
            password = kw["password"]
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
                return {
                    "status": 200,
                    "token": key,
                    "is_employee": is_employee,
                }
        except Exception as e:
            return { "status": 401, "message": f"login failed: {e}"}

    @http.route("/api/logout", type="http", auth="bearer_token", methods=['POST'], csrf=False)
    def logout(self):
        try:
            if request.uid:
                check_api_token = request.env["auth.api.token"].search([('user_id', '=', request.uid)])
                if check_api_token:
                    request.session.logout(keep_db=True)
                    check_api_token.sudo().unlink()        
                    return jsonResponse({"status": 200, "message": "Logout successfully"}, 200 )
        except Exception as e:
             return jsonResponse({ "status": 400, "message": f"Error unexpected: {e}"}, 400)
