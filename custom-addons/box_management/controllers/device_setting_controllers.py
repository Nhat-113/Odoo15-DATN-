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

            request.env.cr.execute("""
                            SELECT 
                                m1.id as id,
                                m1.name,
                                m1.start_time,
                                m1.end_time,
                                m1.mon,
                                m1.tue,
                                m1.wed,
                                m1.thu,
                                m1.fri,
                                m1.sat,
                                m1.sun,
                                m1.status,
                                m2.active,
                                m2.write_date
                            FROM setting_device AS m1
                            LEFT JOIN schedule_device_rel AS m2 ON m1.id = m2.schedule_id
                            WHERE m2.device_id = %(device_id)s
                            AND (m1.write_date > %(time_sync)s OR m2.write_date > %(time_sync)s)
                            ORDER BY m1.id
                        """,{"time_sync": last_synced_timestamp, "device_id": device_id})

            result = request.env.cr.dictfetchall()

            latest_records = []
            if result:
                settings_sorted = sorted(result, key=lambda rec: rec['write_date'], reverse=True)
                unique_records = {}
                
                for record in settings_sorted:
                    key = (record['start_time'], record['end_time'], record['mon'], record['tue'], \
                        record['wed'], record['thu'], record['fri'], record['sat'], record['sun'])
                    if key not in unique_records:
                        unique_records[key] = record

                latest_records = list(unique_records.values())

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            response_data = {
                "status": 200,
                "data": [
                    {
                        "id": item['id'],
                        "name": item['name'],
                        "start_time": item['start_time'] + ":00",
                        "end_time":item['end_time'] + ":00",
                        "days": [x for x,y in zip(days, get_day_of_week_value(item)) if y],
                        "active": True if item['active'] and item['status'] == "active" else False
                    }
                    for item in latest_records
                ]
            }
            return response_data
                
        except Exception as e:
            return {"status": 400, "message": f"Error unexpected: {e}"}