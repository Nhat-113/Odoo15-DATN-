from odoo import http
from odoo.http import request, JsonRequest
from datetime import datetime
from helper.helper import alternative_json_response_for_mobile, jsonResponse, valid_timezone_for_mobile, message_error_missing, check_field_missing_api, get_avatar_model
from helper.attendance_common import handle_attendance_view_mode
import logging

_logger = logging.getLogger(__name__)


class CompanyLocation(http.Controller):

    @http.route('/api/company/location', auth='bearer_token', type='http', methods=["GET"])
    def get_company_location(self, **kw):
        try: 
            log_data = {'GET': '/api/company/location'}
            get_employee = request.env.user.employee_id
            if not get_employee.id :
                res = {"status": 40301, "message": "This user is not an employee"}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 403)
                
            get_location_company = request.env["company.location"].sudo().search([("employee_ids", "=", get_employee.id)])
            
            result = {
                "status": 200,
                "data": [
                    {
                        "id": location.id,
                        "name_company": location.company_id.name,
                        "logo": get_avatar_model('res.company', location.company_id.id),
                        "long": location.lng,
                        "lat": location.lat,
                        "acceptance_distance": location.acceptance_distance,
                        "wifi_access": location.wifi_access,
                        "ssids": [wifi.ssid for wifi in location.wifi_ids]
                    } for location in get_location_company 
                ] 
            }
            _logger.info({**log_data, **result})
            return jsonResponse(result, 200)
        except Exception as e:
            res = {"status": 40002, "message": f"Error unexpected {e}"}
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/employee/app-attendances", auth="bearer_token", type="json", methods=["POST"])
    def mobile_attendances(self, **kw):
        request._json_response = alternative_json_response_for_mobile.__get__(request, JsonRequest)
        try:           
            kw = request.jsonrequest
            log_data = {**{'POST': '/api/employee/app-attendances'}, **kw}
            get_employee = request.env.user.employee_id
            if not get_employee.id:
                res = {"status": 40301, "message": "Employee is not authorized to access"}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 403)
    
            checks = ['faceimage','location_id','timezone','timestamp']
            check_exist = check_field_missing_api(kw, checks)
            if len(check_exist) > 0:
                res = {"status": 40001, "message": f"{message_error_missing(check_exist)}"}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)

            location_id = kw.get("location_id")
            if not isinstance(location_id, int):
                res = {"status": 40001, "message": f"The location_id value is invalid."}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)

            get_location_company = request.env["company.location"].search([("id", "=", location_id)])
            if not get_location_company:
                res = {"status": 40002, "message": f"The specified location (ID: {location_id}) doesn't exist."}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)
            
            employee_id = get_employee.id
            if not get_location_company.employee_ids.filtered(lambda x: x.id == employee_id).id:
                res = {"status": 40101, "message": f"This employee is not authorized to access to company '{get_location_company.company_id.name}' location."}
                _logger.info({**log_data, **res})
                return jsonResponse(res, 401)

            formatted_time = valid_timezone_for_mobile(kw.get("timezone"), kw.get("timestamp"))

            if isinstance(formatted_time, dict):
                _logger.info({**log_data, **formatted_time})
                return jsonResponse(formatted_time, 400)

            # optional field
            datas = {
                "employee_id": get_employee,
                "device_type": "box_io",
                "location_id": location_id,
                "timezone": kw.get("timezone"),
                "timestamp": kw.get("timestamp"),
                "timeutc": formatted_time,
            }

            message = handle_attendance_view_mode(datas)
            res = {"status": 200, "message": message + " successfully"}
            _logger.info({**log_data, **res})
            return jsonResponse(res, 200)
        except Exception as e:
            res = {"status": 40002, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
