# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request, JsonRequest
from datetime import datetime, timedelta
from odoo.tools import html_escape
from helper.helper import alternative_json_response, message_error_missing, check_field_missing_api, jsonResponse, validate_pagination, valid_timezone
from helper.attendance_common import handle_attendance_view_mode
from odoo.addons.web.controllers.main import Session, _serialize_exception
from pytz import timezone

import json
import logging

_logger = logging.getLogger(__name__)


class HrAttendance(http.Controller):
    @http.route("/api/facelog/attendance_odoo", auth="api_key", type="json")
    def facelog_attendances(self, **kw):
        log_data = {**{http.request.httprequest.method: '/api/facelog/attendance_odoo'}, **kw}

        if kw["is_checkin"] == "" or kw["date_time"] == "" or kw["email"] == "":
            res = {"status": 400, "message": "Missing parameter"}
            _logger.info({**log_data, **res})
            return jsonResponse({"message": res["message"]}, res["status"])
        else:
            # Fixme: get config domain email with comapy
            # email = kw['nick_name'] + '@d-soft.com.vn'
            email = kw["email"]
            employees = request.env["hr.employee"].search([("work_email", "=", email)])
            if len(employees):
                # convert string to datetime
                try:
                    date_time = datetime.strptime(
                        kw["date_time"], "%m/%d/%Y, %H:%M:%S"
                    )
                except:
                    res = {"status": 500, "message": "Value input does not match format '%m/%d/%Y, %H:%M:%S"}
                    _logger.info({**log_data, **res})
                    return jsonResponse({"message": res["message"]}, res["status"])
                # convert local+7 to UTC+0
                date_time = date_time - timedelta(hours=7)

                if kw["is_checkin"] == "True" or kw["is_checkin"] == "False":
                    """ verifies if check_in is earlier than check_out. """
                    if employees.attendance_ids:
                        attendance = employees.attendance_ids[
                            employees.attendance_ids.ids.index(
                                max(employees.attendance_ids.ids)
                            )
                        ]
                        if attendance.check_in and date_time < attendance.check_in and kw["is_checkin"] == "False":
                            res = {"status": 402, "message": "'Check Out' cannot be earlier than 'Check In'"}
                            _logger.info({**log_data, **res})
                            return jsonResponse({"message": res["message"]}, res["status"])
                        
                    result = request.env["hr.employee"].attendance_manual_api(employees,date_time,"hr_attendance.hr_attendance_action_my_attendances",kw["is_checkin"],)
                else:
                    res = {"status": 404, "message": "is_checkin param does not match format boolean"}
                    _logger.info({**log_data, **res})
                    return jsonResponse({"message": res["message"]}, res["status"])

                response_message = result["action"]["attendance"]
                response = {
                    "id": response_message["id"],
                    "employee_id": response_message["employee_id"],
                    "check_in": response_message["check_in"],
                    "check_out": response_message["check_out"],
                    "worked_hours": response_message["worked_hours"],
                }
                _logger.info({**log_data, **{"status": 200}, **response})
                return {"status": 200, "message": response}
            else:
                res = {"status": 400, "message": "User does not exist"}
                _logger.info({**log_data, **res})
                return res

    @http.route("/api/attendances/getuser", auth="api_key", type="json")
    def facelog_getuser(self, **kw):
        try:
            log_data = {**{http.request.httprequest.method: '/api/attendances/getuser'}, **kw}
            # email = kw['nick_name'] + '@d-soft.com.vn'
            email = kw["email"]
            employee = request.env["hr.employee"].search([("work_email", "=", email)])
            if not employee:
                res = {"status": 400, "message": "User does not exits"}
                _logger.info({**log_data, **res})
                return res
            response = {
                "status": 200,
                "message": "Request success",
                "values": {"full_name": employee.name, "birth_day": employee.birthday},
            }
            _logger.info({**log_data, **response})
            return response
        except:
            if not kw["email"] and not kw:
                res = {"status": 404, "message": "Missing email parameter"}
                _logger.info({**log_data, **res})
                return res
            else:
                res = {"status": 400, "massage": "Missing parameter"}
                _logger.info({**log_data, **res})
                return res

    # @http.route("/api/attendances/get_public_holiday", auth="public", type="json")
    # def facelog_get_public_holiday(self, **kw):
    #     try:
    #         if kw:
    #             return {
    #                 "status": 400,
    #                 "massage": "No need any parameters",
    #             }
    #         else:
    #             vals = []
    #             public_holiday = request.env["resource.calendar.leaves"].search(
    #                 [("resource_id", "=", False), ("holiday_id", "=", False)]
    #             )
    #             for record in public_holiday:
    #                 holiday = {
    #                     "item": record.name,
    #                     "date_from": record.date_from + timedelta(hours=7),
    #                     "date_to": record.date_to + timedelta(hours=7),
    #                 }
    #                 vals.append(holiday)

    #             return jsonResponse({"message": "Request success", "values": vals}, 200) 
    #     except:
    #         return jsonResponse({"message": "Odoo Server Error"}, 500)

    ## latest api version 03/2024
    @http.route("/api/employee/attendances", auth="api_key", type="json", methods=["POST"])
    def facelog_attendances_v2(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'POST': '/api/employee/attendances'}, **kw}
            
            if not kw.get('email'):
                res = {"status": 400, "message": "Missing required parameter email"}
                _logger.info({**log_data, **res})
                return res
            
            if not kw.get('device_id'):
                res = {"status": 400, "message":"Missing required parameter device_id"}
                _logger.info({**log_data, **res})
                return res

            email = kw.get("email")
            device_id = kw.get("device_id")

            device = request.env['box.management'].sudo().search([("device_id", "=", device_id)])

            if not device:
                res = {"status": 400, "message": f"Device ID {device_id} isn't registered on the server."}
                _logger.info({**log_data, **res})
                return res
            
            box_types = request.env['box.management']._fields['device_type'].selection
            box_types = [item[0] for item in box_types]

            if  not kw.get('device_type') or kw.get('device_type') not in box_types:
                res = {"status": 400, "message": "Missing or invalid required parameter device_type"}
                _logger.info({**log_data, **res})
                return res

            formatted_time = valid_timezone(kw.get("timezone"), kw.get("timestamp"))
            if isinstance(formatted_time, datetime) is False:
                res = formatted_time
                _logger.info({**log_data, **res})
                return res
        
            employee = request.env["hr.employee"].sudo().search([("work_email", "=", email)])
            if not employee:
                res = {"status": 400, "message": "User does not exits"}
                _logger.info({**log_data, **res})
                return res
            
            # optional field
            position = kw.get("position") if not kw.get("position") else str(kw.get("position"))
            datas = {
                "employee_id": employee,
                "device_type": kw.get("device_type"),
                "device_id": device.id,
                "timezone": kw.get("timezone"),
                "timestamp": kw.get("timestamp"),
                "timeutc": formatted_time,
                "position": position
            }
            message = handle_attendance_view_mode(datas)
            
            res = {"status": 200, "message": message + " successfully"}
            _logger.info({**log_data, **res})
            return res
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res

    @http.route("/api/attendance/xlsx_reports", type="http", auth="user", methods=["GET"])
    def export_excel_report(self, **kw):
        log_data = {**{'GET': '/api/attendance/xlsx_reports'}, **kw}

        data = json.loads(kw.get("kw"))
        model = data['model']
        options = data['options']
        output_format = data['output_format']
        options = json.loads(options)
        file_model = request.env[model]
        file_data = file_model.action_get_data(options["start_date"], 
                                               options["end_date"], 
                                               options['allowed_companies'])
        
        time_off_data = file_model.approved_time_off_query(options['allowed_companies'], options["start_date"], options["end_date"])

        options["data"] = file_data
        try:
            if output_format == "xlsx":
                response = request.make_response(
                    None,
                    headers=[
                        (
                            "Content-Type",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        ),
                        (
                            "Content-Disposition",
                            f"attachment; filename=Attendance_report_{options['start_date']}_{options['end_date']}.xlsx",
                        ),
                    ],
                    cookies=None,
                )
                file_model.generate_xlsx_report(options, response, options['allowed_companies'], time_off_data)
            
            _logger.info({**log_data, **{'status': 200}})
            return response

        except Exception as e:
            se = _serialize_exception(e)
            error = {"code": 200, "message": "Odoo Server Error", "data": se}
            _logger.info({**log_data, **error})

            return request.make_response(html_escape(json.dumps(error)))

    @http.route("/api/health", type="http", auth="api_key", methods=["GET"])
    def health_check(self, **kw):
        msg = jsonResponse({"message": "OK"}, 200)
        return msg


class SessionCustom(Session):
    @http.route("/web/session/authenticate/api_attendances_key", type="json", auth="public", sitemap=False)
    def authenticate(self, **uid):
        log_data = {**{http.request.httprequest.method:'/web/session/authenticate/api_attendances_key'}, **uid}
        try:
            if uid:
                user = request.env["auth.api.key"].search(
                    [("user_id", "=", uid["uid"])], limit=1
                )
                api_key = user.key
            else:
                res = {
                    "status": 404,
                    "message": "Missing uid parameter",
                }
                _logger.info({**log_data, **res})
                return jsonResponse({"message": res['message']}, res["status"])
        except:
            api_key = None

        if api_key:
            value = {
                "value": {
                    "message": "Connect Success",
                    "api_key": api_key,
                    "user": user.user_id.display_name,
                },
            }
            _logger.info({**log_data, **{"status": 200}, **value})
            return jsonResponse(value, 200)
        else:
            res = {
                "status": 400,
                "message": "Nothing api key mapping with uid parameter",
            }
            _logger.info({**log_data, **res})
            return jsonResponse({"message": res['message']}, res["status"])


##HR Employee api
class HrEmployees(http.Controller):

    @http.route('/api/employee/list', auth='api_key', type='json', methods=["GET"])
    def get_list_employees(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'GET': '/api/employee/list'}, **kw}

            offset = kw["page"]
            limit = kw["per_page"]
            records_to_skip = (offset - 1) * limit
            # get total record in table employee
            total_records = request.env["hr.employee"].sudo().search_count([])

            # caculate total page of list employee
            last_pages = -(-total_records // limit) 

            if offset > last_pages:
                response_data = {
                    "employees": [],
                    "current_page": offset,
                    "last_page": last_pages,
                    "per_page": limit,
                    "total": total_records,
                }
            else:
                employees = (
                    request.env["hr.employee"]
                    .sudo()
                    .search([], order="id", offset=records_to_skip, limit=limit)
                )
                response_data = {
                    "status": 200,
                    "employees": [
                        {
                            "employee_id": employee.id,
                            "email": employee.work_email,
                            "fullname": employee.name,
                            "faceimage": employee.image_1920
                            if employee.image_1920
                            else None,
                            "fingerprint_template": employee.fingerprint_template
                            if employee.fingerprint_template
                            else None,
                            "active": employee.active,
                        }
                        for employee in employees
                    ],
                    "current_page": offset,
                    "last_page": last_pages,
                    "per_page": limit,
                    "total": total_records,
                }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res

    @http.route("/api/employee/update_employee_infor", auth="api_key", type="json", methods=["POST"])
    def update_faceimage(self):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'POST': '/api/employee/update_employee_infor'}, **kw}

            email = kw.get("email")
            image = kw.get("data")
            type = kw.get("type")
          
            if not image:
                res = {"status": 400, "message": "Can not update image is null"}
                _logger.info({**log_data, **res})
                return res


            employee = request.env["hr.employee"].sudo().search([("work_email", "=", email)])

            if not employee:
                res = {"status": 400, "message": "User does not exits"}
                _logger.info({**log_data, **res})
                return res

            formatted_time = valid_timezone(kw.get("timezone"), kw.get("timestamp"))
            if isinstance(formatted_time, datetime) is False:
                _logger.info({**log_data, **formatted_time})
                return formatted_time
            
            if type not in ['face','fingerprint']:
                error_type_text = ' | '.join(['face','fingerprint'])
                res = {"status": 400, "message": f'The type value must include one of the following options: {error_type_text}'}
                _logger.info({**log_data, **res})
                return res

            if type == "face":
                employee.write({ "image_1920": image })
            elif type == "fingerprint":
                employee.write({ "fingerprint_template": image })
            
            res = {"status": 200, "message": f"{type} updated successfully"}
            _logger.info({**log_data, **res})
            return res
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res
        
    @http.route('/api/device/sync_employee', auth='api_key', type='json', methods=['GET'])
    def get_list_employees_update(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        kw = request.jsonrequest
        log_data = {**{'GET': '/api/device/sync_employee'}, **kw}
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if params is False:
            res = {"status": 400, "message": "Page or Per_page must be an integer number"}
            _logger.info({**log_data, **res})
            return res
        try:
            check_exist = check_field_missing_api(kw, ["last_synced_timestamp", "timezone", "device_id"])
            
            if len(check_exist) > 0:
                res = {"status": 400, "message":  message_error_missing(check_exist)}
                _logger.info({**log_data, **res})
                return res

            offset = params["offset"]
            limit = params["limit"]
            device_id = kw.get('device_id')
            records_to_skip = (offset - 1) * limit
            
            last_synced_timestamp = valid_timezone(kw.get("timezone"), kw.get("last_synced_timestamp"))

            if isinstance(last_synced_timestamp, datetime) is False:
                _logger.info({**log_data, **last_synced_timestamp})
                return last_synced_timestamp

            device = request.env['box.management'].sudo().search([("device_id", "=", device_id)], limit=1)
            if not device:
                res = {"status": 400, "message": f"Device ID {device_id} isn't registered on the server."}
                _logger.info({**log_data, **res})
                return res
            # get_status_access = request.env['box.employee.rel'].sudo().search([("device_id", "=", device_id), ("write_date", ">", last_synced_timestamp), ("employee_id.id", "in", )])
            request.env.cr.execute("""
                    SELECT COUNT(*) AS total_count
                    FROM hr_employee AS m1
                    LEFT JOIN box_employee_rel AS m2 ON m1.id = m2.employee_id
                    WHERE m2.device_id = %(device_id)s
                    AND (m1.sync_write_date > %(time_sync)s OR m2.write_date > %(time_sync)s)
                """, {"time_sync": last_synced_timestamp, "device_id": device.id})

            total_records = request.env.cr.fetchone()[0]
            request.env.cr.execute("""
                            SELECT 
                                m1.id as id,
                                m1.work_email,
                                m1.name,
                                m1.fingerprint_template,
                                m2.delete_at
                            FROM hr_employee AS m1
                            LEFT JOIN box_employee_rel AS m2 ON m1.id = m2.employee_id
                            WHERE m2.device_id = %(device_id)s
                            AND (m1.sync_write_date > %(time_sync)s OR m2.write_date > %(time_sync)s)
                            ORDER BY m1.id
                            OFFSET %(offset)s
                            LIMIT %(limit)s
                        """,{"time_sync": last_synced_timestamp, "device_id": device.id, "offset": records_to_skip, "limit": limit})
            result = request.cr.dictfetchall()
            # caculate total page of list employee
            last_pages = -(-total_records // limit)
            get_id_employee = [employee['id'] for employee in result]
            employee_result = { emp.id: emp.image_1920 for emp in request.env['hr.employee'].search([('id', 'in', get_id_employee)])}

            response_data = {
                "status": 200,
                "employees": [
                    {
                        "employee_id": employee['id'],
                        "email": employee['work_email'],
                        "fullname": employee['name'],
                        "faceimage": employee_result.get(employee.get('id')),
                        "fingerprint_template": employee["fingerprint_template"] if employee["fingerprint_template"] else None,
                        "active": True if employee["delete_at"] is None and employee_result.get(employee.get('id')) is not None else False,
                    }
                    for employee in result
                ],
                "current_page": offset,
                "last_page": last_pages,
                "per_page": limit,
                "total": total_records,
            }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res

    @http.route("/api/device/check_sync", auth="api_key", type="json", methods=["GET"])
    def check_sync_emp(self, **kw):
        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        try:
            kw = request.jsonrequest
            log_data = {**{'GET': '/api/device/check_sync'}, **kw}
            check_exist = check_field_missing_api(kw, ["last_synced_timestamp", "timezone", "device_id"])
            if len(check_exist) > 0: 
                res = {"status": 400, "message": message_error_missing(check_exist)}
                _logger.info({**log_data, **res})
                return res
            else: 
                device_id = kw.get('device_id')

                last_synced_timestamp = valid_timezone(kw.get('timezone'), kw.get('last_synced_timestamp'))
                if isinstance(last_synced_timestamp, datetime) is False:
                    _logger.info({**log_data, **last_synced_timestamp})
                    return last_synced_timestamp
                
                device = request.env['box.management'].sudo().search([("device_id", "=", device_id)], limit=1)

                if not device:
                    res = {"status": 400, "message": f"Device ID {device_id} isn't registered on the server."}
                    _logger.info({**log_data, **res})
                    return res

                request.env.cr.execute("""
                    SELECT COUNT(*) AS total_count
                    FROM hr_employee AS m1
                    LEFT JOIN box_employee_rel AS m2 ON m1.id = m2.employee_id
                    WHERE m2.device_id = %(device_id)s
                    AND (m1.sync_write_date > %(time_sync)s OR m2.write_date > %(time_sync)s)
                """, {"time_sync": last_synced_timestamp, "device_id": device.id})

                total_emp_update = request.env.cr.fetchone()[0]

                total_passcode_update = request.env['passcode.register'].sudo().with_context(active_test=False).search_count([("device_ids", "=", device_id), ('write_date', '>', last_synced_timestamp)])
                total_setting_update = request.env['setting.device'].sudo().with_context(active_test=False).search_count([("device_ids", "=", device_id), ('write_date', '>', last_synced_timestamp)])
                total_setting_rel_update = request.env['schedule.device.rel'].sudo().with_context(active_test=False).search_count([("device_id", "=", device_id), ('write_date', '>', last_synced_timestamp)])
                response_data = {
                    "status": 200,
                    "employee": "1" if total_emp_update > 0 else "0",
                    "passcode": "1" if total_passcode_update > 0 else "0",
                    "time_setting": "1" if total_setting_update or total_setting_rel_update > 0 else "0" ,
                }
            _logger.info({**log_data, **response_data})
            return response_data
        except Exception as e:
            res = {"status": 400, "message": f"Error unexpected: {e}"}
            _logger.info({**log_data, **res})
            return res
