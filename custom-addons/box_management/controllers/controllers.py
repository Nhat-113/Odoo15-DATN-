from odoo import http
from datetime import datetime
from odoo.http import request, JsonRequest
# from odoo.tools import  config
from pytz import timezone
from helper.helper import alternative_json_response, message_error_missing, check_field_missing_api, convert_current_tz, jsonResponse,logger , valid_timezone

import logging

_logger = logging.getLogger(__name__)


class BoxManagement(http.Controller):
    @http.route("/api/device/register", type="json", auth="api_key", methods=["POST"])
    def create_hr_device(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'POST': '/api/device/register'}, **kw}
            get_device_types_field = request.env['box.management']._fields['device_type'].selection
            device_types = [item[0] for item in get_device_types_field]

            check_exist = check_field_missing_api(kw, ['device_type', 'device_id'])

            if len(check_exist) > 0:
                res = {"status": 400, "message": message_error_missing(check_exist)}
                _logger.info({**log_data, **res})
                return res
            
            device_id = kw.get("device_id")
            device_type = kw.get("device_type")
            device_name = kw.get("device_name")

            if device_id.strip() == "":
                res = {"status": 400, "message": "The device_id value shouldn't be empty"}
                _logger.info({**log_data, **res})
                return res

            if device_type not in device_types:
                error_type_text = ' | '.join(device_types)
                res = {"status": 400 ,"message":  f'The device_type value must include one of the following options: {error_type_text}'}
                _logger.info({**log_data, **res})
                return res
            
            device_exist = request.env['box.management'].sudo().search([('device_id', '=', device_id)])
            if device_exist.id: 
                res = {"status": 400, "message": "The Box already exists with the device ID: %s" %(device_id)}
                _logger.info({**log_data, **res})
                return res

            device_data = {
                "device_id": device_id,
                "device_name": '' if device_name is None else device_name,
                "device_type": device_type,
            }
            request.env['box.management'].sudo().create(device_data)
            response_data = {
                "status": 200,
                "message": "Registered box successfully"
            }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res
        
    @http.route("/api/device/register", type="json", auth="api_key", methods=["PUT"])
    def update_box(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'PUT': '/api/device/register'}, **kw}
            get_device_types_field = request.env['box.management']._fields['device_type'].selection
            device_types = [item[0] for item in get_device_types_field]

            check_exist = check_field_missing_api(kw, ['device_type', 'device_id'])

            if len(check_exist) > 0:
                res = {"status": 400, "message": message_error_missing(check_exist)}
                _logger.info({**log_data, **res})
                return res
            
            device_id =  kw.get("device_id")
            device_type =  kw.get("device_type")
            device_name = kw.get("device_name")
            
            if device_id.strip() == "":
                res = {"status": 400, "message": "The device_id value shouldn't be empty"}
                _logger.info({**log_data, **res})
                return res
        
            if device_type not in device_types:
                error_type_text = ' | '.join(device_types)
                res = {"status": 400, "message": f'The device_type value must include one of the following options: {error_type_text}'}
                _logger.info({**log_data, **res})
                return res

            device_exist = request.env['box.management'].sudo().search([('device_id', '=', device_id)])

            if device_exist.id is False:
                res = {"status": 404, "message": f"The Box not exists with the device ID: {device_id}"}
                _logger.info({**log_data, **res})
                return res
            
            if device_exist.device_type == device_type:
                res = {"status": 400, "message": f"The Box has already been assigned the device type: {device_id}"}
                _logger.info({**log_data, **res})
                return res
                   
            device_exist.write({
                "device_type": device_type,
            } if device_name is None else {
                "device_type": device_type,
                "device_name": device_name
            })

            response_data = {
                "status": 200,
                "message": "Updated box successfully",
            }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res
        
    @http.route("/api/device/sync_passcode", type="json", auth="api_key", methods=["GET"])
    def sync_passcode(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'GET': '/api/device/sync_passcode'}, **kw}
            check_exist = check_field_missing_api(kw, ['last_synced_timestamp', 'timezone', 'device_id'])

            if len(check_exist) > 0:
                res = {"status": 400, "message": message_error_missing(check_exist)}
                _logger.info({**log_data, **res})
                return res

            device_id =  kw.get("device_id")

            last_synced_timestamp = valid_timezone(kw.get("timezone"), kw.get("last_synced_timestamp"))
            if isinstance(last_synced_timestamp, datetime) is False:
                _logger.info({**log_data, **last_synced_timestamp})
                return last_synced_timestamp
            
            passcodes = request.env['passcode.register'].sudo().with_context(active_test=False).search([("device_ids", "=", device_id), ('write_date', '>', last_synced_timestamp)])
            response_data = {
                "status": 200,
                "passcodes": [
                    {
                        "id": passcode_item.id,
                        "code": passcode_item.passcode,
                        "start_time": convert_current_tz(kw.get("timezone") ,passcode_item.valid_from),
                        "expiration_time": convert_current_tz(kw.get("timezone"), passcode_item.expired_date),
                        "active": passcode_item.active
                    }
                    for passcode_item in passcodes
                ]
            }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res
