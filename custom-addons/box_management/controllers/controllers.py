from odoo import http
from datetime import datetime
from odoo.http import request, JsonRequest
# from odoo.tools import  config
from pytz import timezone
from helper.helper import alternative_json_response, message_error_missing, check_field_missing_api, convert_current_tz, jsonResponse,logger , valid_timezone


class BoxManagement(http.Controller):
    @http.route("/api/device/register", type="json", auth="api_key", methods=["POST"])
    def create_hr_device(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            get_device_types_field = request.env['box.management']._fields['device_type'].selection
            device_types = [item[0] for item in get_device_types_field]

            check_exist = check_field_missing_api(kw, ['device_type', 'device_id'])

            if len(check_exist) > 0:
                return {"status": 400, "message": message_error_missing(check_exist)} 
            
            device_id = kw.get("device_id")
            device_type = kw.get("device_type")
            device_name = kw.get("device_name")

            if device_id.strip() == "":
                return  {"status": 400, "message": "The device_id value shouldn't be empty", }

            if device_type not in device_types:
                error_type_text = ' | '.join(device_types)
                return {"status": 400 ,"message":  f'The device_type value must include one of the following options: {error_type_text}'}
            
            device_exist = request.env['box.management'].sudo().search([('device_id', '=', device_id)])
            if device_exist.id: 
                return  {"status": 400, "message": "The Box already exists with the device ID: %s" %(device_id)}

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
            # _logger.info('call api success: /api/register_devices, body: ' + json.dumps(kw))
            return response_data
        except Exception as e:
            # _logger.error('call api false: /api/register_devices body: ' + json.dumps(kw), exc_info=True)
            return {"status": 400, "message": f"Error unexpected: {e}"}
        
    @http.route("/api/device/register", type="json", auth="api_key", methods=["PUT"])
    def update_box(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            get_device_types_field = request.env['box.management']._fields['device_type'].selection
            device_types = [item[0] for item in get_device_types_field]

            check_exist = check_field_missing_api(kw, ['device_type', 'device_id'])

            if len(check_exist) > 0:
               return {"status": 400, "message": message_error_missing(check_exist)}
            
            device_id =  kw.get("device_id")
            device_type =  kw.get("device_type")
            device_name = kw.get("device_name")
            
            if device_id.strip() == "":
                return {"status": 400, "message": "The device_id value shouldn't be empty"}
        
            if device_type not in device_types:
                error_type_text = ' | '.join(device_types)
                return {"status": 400, "message": f'The device_type value must include one of the following options: {error_type_text}'}

            device_exist = request.env['box.management'].sudo().search([('device_id', '=', device_id)])

            if device_exist.id is False:
                return {"status": 404, "message": f"The Box not exists with the device ID: {device_id}"}
            
            if device_exist.device_type == device_type:
                return {"status": 400, "message": f"The Box has already been assigned the device type: {device_id}"}
                   
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
            # _logger.info('call api success: /api/register_devices, body: ' + json.dumps(kw))  
            return response_data
        except Exception as e:
            # _logger.error('call api false: /api/register_devices body: ' + json.dumps(kw), exc_info=True)
            return {"status": 400, "message": f"Error unexpected: {e}"}
        
    @http.route("/api/device/sync_passcode", type="json", auth="api_key", methods=["GET"])
    def sync_passcode(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            check_exist = check_field_missing_api(kw, ['last_synced_timestamp', 'timezone', 'device_id'])

            if len(check_exist) > 0:
                return {"status": 400, "message": message_error_missing(check_exist)} 

            device_id =  kw.get("device_id")

            last_synced_timestamp = valid_timezone(kw.get("timezone"), kw.get("last_synced_timestamp"))
            if isinstance(last_synced_timestamp, datetime) is False: 
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
            return response_data
        except Exception as e:
            return {"status": 400, "message": f"Error unexpected: {e}"}
