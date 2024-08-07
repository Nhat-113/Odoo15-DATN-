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
            door_information_list = []
            for door in tenant.door_ids:
                door_information_list.append({
                    'door_name': door.door_name,
                    'door_link': door.door_link
                })
            if tenant:
                data = {
                    'link_domain': tenant.link_domain,
                    'allow_to_open': tenant.allow_to_open,
                    'face_detection_link': tenant.face_detection_link,
                }
                if tenant.allow_to_open:
                    data['door_information_list'] = door_information_list
                else :
                    data.pop("door_information_list", None)
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

        