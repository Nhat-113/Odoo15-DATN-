from odoo import http
from datetime import datetime
from odoo.http import request, JsonRequest
from helper.helper import alternative_json_response, message_error_missing, check_field_missing_api, valid_timezone
from helper.setting_device_common import get_day_of_week_value


class SettingDevice(http.Controller):
    @http.route("/api/device/sync_settings", type="json", auth="api_key", methods=["GET"])
    def get_device_setting(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            check_exist = check_field_missing_api(kw, ['last_synced_timestamp', 'timezone', 'device_id'])

            if len(check_exist) > 0:
                return {"status": 400, "message": message_error_missing(check_exist)} 
            
            device_id = kw.get("device_id")

            last_synced_timestamp = valid_timezone(kw.get("timezone"), kw.get("last_synced_timestamp"))
            if isinstance(last_synced_timestamp, datetime) is False: 
                return last_synced_timestamp

            settings = request.env['setting.device'].search([
                ("device_ids", "=", device_id),
                ('write_date', '>', last_synced_timestamp)
            ])
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            response_data = {
                "status": 200,
                "data": [
                    {
                        "name": item.name,
                        "start_time": item.start_time + ":00",
                        "end_time":item.end_time + ":00",
                        "days": [x for x,y in zip(days, get_day_of_week_value(item)) if y],
                    }
                    for item in settings
                ]
            }
            return response_data
                
        except Exception as e:
            return {"status": 400, "message": f"Error unexpected: {e}"}