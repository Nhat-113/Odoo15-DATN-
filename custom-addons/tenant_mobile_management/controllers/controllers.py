from odoo import http
from odoo.http import request
from helper.helper import jsonResponse

class check_api(http.Controller):

    @http.route("/api/mobile/tenant", type="http", auth='public', methods=['GET'])
    def get_domain_by_server_name(self, **kw):
        try:
            if not kw.get("server_name"):
                return jsonResponse({
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": "Missing tenant server name"
                }, 400)

            tenant = request.env["tenant.management"].sudo().search([('server_name', '=', kw.get("server_name"))])
            box_login_infor = {
                'box_username': tenant.box_username or '',
                'box_password': tenant.box_password or '',
                'box_url': tenant.box_url or ''
            }
            device_information_list = [
                {
                    'device_name': device.name,
                    'device_id': device.device_id,
                    'device_description': device.description or ''
                } for device in tenant.device_ids]

            if tenant:
                data = {
                    'link_domain': tenant.link_domain,
                    'allow_to_open': tenant.allow_to_open,
                    'face_detection_link': tenant.face_detection_link or '',
                    'box_login_infor': {},
                    'device_information_list': []
                }
                if tenant.allow_to_open:
                    data['device_information_list'] = device_information_list
                    data['box_login_infor'] = box_login_infor
                return jsonResponse(data, 200)
            else:
                return jsonResponse({
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": "Invalid tenant server name"
                    }, 400)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

        