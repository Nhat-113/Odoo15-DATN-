from odoo import http
from odoo.http import request, JsonRequest
from datetime import datetime
from helper.helper import alternative_json_response_for_mobile, jsonResponse, valid_timezone_for_mobile, message_error_missing, check_field_missing_api
from helper.attendance_common import handle_attendance_view_mode

class CompanyLocation(http.Controller):

    @http.route('/api/company/location', auth='bearer_token', type='http', methods=["GET"])
    def get_company_location(self, **kw):
       try: 
            get_employee = request.env.user.employee_id
            if not get_employee.id :
                return jsonResponse({"status": 40301, "message": "This user is not an employee"}, 403)
                
            get_location_company = request.env["company.location"].sudo().search([("employee_ids", "=", get_employee.id)])
            
            result = {
                "status": 200,
                "data": [
                    {
                        "id": location.id,
                        "name_company": location.company_id.name,
                        "long": location.lng,
                        "lat": location.lat,
                        "acceptance_distance": location.acceptance_distance,
                        "wifi_access": location.wifi_access,
                        "ssids": [wifi.ssid for wifi in location.wifi_ids]
                    } for location in get_location_company 
                ] 
            }
            return jsonResponse(result, 200)
       except Exception as e:
            return jsonResponse({"status": 40002, "message": f"Error unexpected {e}"}, 400)

    @http.route("/api/employee/app-attendances", auth="bearer_token", type="json", methods=["POST"])
    def mobile_attendances(self, **kw):
        request._json_response = alternative_json_response_for_mobile.__get__(request, JsonRequest)
        try:           
            kw = request.jsonrequest
            get_employee = request.env.user.employee_id
            if not get_employee.id:
                return jsonResponse({"status": 40301, "message": "Employee is not authorized to access"}, 403)
    
            checks = ['faceimage','location_id','timezone','timestamp']
            check_exist = check_field_missing_api(kw, checks)
            if len(check_exist) > 0:
                return jsonResponse({"status": 40001, "message": f"{message_error_missing(check_exist)}"}, 400)

            location_id = kw.get("location_id")
            if not isinstance(location_id, int):
                return jsonResponse({"status": 40001, "message": f"The location_id value is invalid."}, 400)

            get_location_company = request.env["company.location"].search([("id", "=", location_id)])
            if not get_location_company:
                return jsonResponse({"status": 40002, "message": f"The specified location (ID: {location_id}) doesn't exist."}, 400)
            
            employee_id = get_employee.id
            if not get_location_company.employee_ids.filtered(lambda x: x.id == employee_id).id:
                return jsonResponse({"status": 40101, "message": f"This employee is not authorized to access to company '{get_location_company.company_id.name}' location."}, 401)

            formatted_time = valid_timezone_for_mobile(kw.get("timezone"), kw.get("timestamp"))

            if isinstance(formatted_time, dict):
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
            return jsonResponse({"status": 200, "message": message + " successfully"}, 200)
        except Exception as e:
            return jsonResponse({"status": 40002, "message": f"Error unexpected: {e}"}, 400)
