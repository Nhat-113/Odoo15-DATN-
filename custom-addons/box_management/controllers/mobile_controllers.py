from odoo import http
from datetime import datetime, timedelta
from odoo.http import request
from dateutil.relativedelta import relativedelta
# from odoo.tools import  config
import pytz
from helper.helper import message_error_missing, check_field_missing_api, jsonResponse, convert_current_tz, check_authorize, handle_pagination, validate_pagination, image_url_getter, is_valid_month, is_valid_integer, check_and_handle_missing_fields

TIME_FORMAT = "%Y-%m-%d, %H:%M:%S"
role_attendance = [
    {
        "role_name": "group_hr_attendance",
        "description": "Manual Attendance: own attendances"
    }, {
        "role_name": "group_hr_attendance_user",
        "description": "attendance officer: full access"
    }, {
        "role_name": "group_hr_attendance_manager",
        "description": "admin attendance: full access, configuration attendance"
    }]

class BoxManagementMobile(http.Controller):

    @http.route('/api/me', auth='bearer_token', type='http', methods=["GET"])
    def get_current_user(self, **kw):
        try:            
            user = request.env.user
            
            attendance_role = {
                "role_name": "",
                "description": ""
            }
            for permit in role_attendance:
                check_permission = user.has_group(f"hr_attendance.{permit.get('role_name')}")
                if check_permission:
                    attendance_role = permit

            data = {
                "avatar": image_url_getter('res.users', request.uid),
                "role": attendance_role
            }
            
            fields_map = {
                "id": "id",
                "fullname": "display_name",
                "email": "email",
                "work_phone": "work_phone",
                "mobile_phone": "mobile_phone",
                "job": "job_title"
            }

            for key, field in fields_map.items():
                value = getattr(user, field)
                data[key] = value if value else ""
        
            obj_fields_map = [
                ("company", "company_id"),
                ("department", "department_id"),
                ("manager", "employee_parent_id"),
                ("coach", "coach_id")
            ]
            
            check_leave_manager_id = hasattr(user, 'leave_manager_id')

            if check_leave_manager_id:
                obj_fields_map.append(("timeoff", "leave_manager_id"))

            for key, field in obj_fields_map:
                value = getattr(user, field)
                data[key] = {"id": value.id, "name": value.name} if value else None

            return jsonResponse({"data": data}, 200)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
                }, 400)

    @http.route("/api/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_info(self, employee_id, **kwargs):
        try:
            user = request.env.user
            request_user_id = request.uid
            if not check_authorize('hr.employee', request_user_id):
                employee = request.env['hr.employee.public'].search([('id', '=', employee_id)])
            else:
                employee = request.env['hr.employee'].search([('id', '=', employee_id)])

            if not employee:
                return jsonResponse({
                    "status": 40401,
                    "message": "Not found",
                    "keyerror": "Employee Not Found"
                }, 404)
            
            data = { "avatar": image_url_getter('hr.employee', employee.id) }
            fields_map = {
                "id": "id",
                "fullname": "name",
                "email": "work_email",
                "work_phone": "work_phone",
                "mobile_phone": "mobile_phone",
                "job": "job_title"
            }

            for key, field in fields_map.items():
                value = getattr(employee, field)
                data[key] = value if value else ""

            obj_fields_map = [
                ("company", "company_id"),
                ("department", "department_id"),
                ("manager", "parent_id"),
                ("coach", "coach_id"),
            ]

            check_leave_manager_id = hasattr(user, 'leave_manager_id')

            if check_leave_manager_id:
                obj_fields_map.append(("timeoff", "leave_manager_id"))

            for key, field in obj_fields_map:
                value = getattr(employee, field)
                data[key] = {"id": value.id, "name": value.name} if value else None

            return jsonResponse({"data": data}, 200)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

    @http.route("/api/attendance/employee", type="http", auth="bearer_token", methods=["GET"])
    def get_attendance_data(self, **kwargs):
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        if not params:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }, 400)
        try:
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                return jsonResponse({
                    "status": 40301,
                    "message": "Forbidden",
                    "keyerror": "Access Denied"
                }, 403)
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                return jsonResponse({
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": message_error_missing(missing_fields)
                }, 400)
            
            
            date_str = kwargs.get('date')
            date = datetime.strptime(date_str, "%Y-%m-%d")
            name = kwargs.get('name')
            company_name = kwargs.get('company_name')
            type = kwargs.get('type', 'all')
            offset = params["offset"]
            limit = params["limit"]
            records_to_skip = (offset - 1) * limit
            
            search_domain = [('location_date', '=', date)]

            if name:
                search_domain.append(('employee_id.name', 'ilike', name))
            if company_name:
                search_domain.append(('employee_id.company_id.name', 'ilike', company_name))

            total_search_records = request.env['hr.attendance'].read_group(
                groupby=['employee_id'],  # Specify 'employee_id' for grouping
                fields=['employee_id:count(distinct employee_id)'],
                domain=search_domain,  # Include the original search domain
                lazy=False
            )
            total_records = len(total_search_records)

            attds = request.env['hr.attendance'].read_group(
                groupby=['employee_id'],  # Group by employee_id
                fields=['check_in:min', 'check_out:max'],  # Get the latest checkin and earliest checkout
                domain=search_domain,  # Apply the original search domain
                offset=records_to_skip,
                limit=limit
            )
            employee_ids = [emp.get("employee_id")[0] for emp in attds]

            employees = request.env["hr.employee"].sudo().search([
                ("id", "in", employee_ids),
                ("active", "=", True)
            ])  
            attendances = []

            if employees:
                current_tz = request.env.user.tz
                for employee in employees:
                    attd = list(filter(lambda x: x.get('employee_id')[0] == employee['id'], attds))

                    entry = {
                        "employee_id": employee["id"],
                        "employee_name": employee["name"],
                        "job_title": employee["job_title"] if employee["job_title"] else "",
                        "avatar": image_url_getter('hr.employee', employee["id"]),
                    } 
                    first_check_in = convert_current_tz(current_tz, attd[0]['check_in']).strftime(TIME_FORMAT)
                    last_check_out = convert_current_tz(current_tz, attd[0]['check_out']).strftime(TIME_FORMAT) if attd[0]['check_out'] else ""
                    if type == 'checkin':
                        entry["check_in"] = first_check_in
                    elif type == 'checkout':
                        entry["check_out"] = last_check_out
                    else: 
                        entry["check_in"] = first_check_in
                        entry["check_out"] = last_check_out
                    # duration_seconds = (attd['last_check_out'] - attd['first_check_in']).total_seconds() if attd['last_check_out'] else 0
                    # duration = str(timedelta(seconds=duration_seconds))
                    # entry["duration"] = duration
                    attendances.append(entry)
            return jsonResponse({
                "attendances": attendances,
                "pagination": handle_pagination(offset, limit, total_records)
                }, 200)  
        
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

    @http.route("/api/attendance/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_attendances(self, employee_id, **kwargs):
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        if not params:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }, 400)
        try:
            current_tz = request.env.user.tz
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                return jsonResponse({"message": "Access Denied"}, 403)
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                return jsonResponse({
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": message_error_missing(missing_fields)
                }, 400)
            
            date_str = kwargs.get('date')
            date = datetime.strptime(date_str, "%Y-%m-%d")
            offset = params["offset"]
            limit = params["limit"]
            records_to_skip = (offset - 1) * limit
            
            search_domain = [
                ('employee_id', '=', employee_id),
                ('location_date', '>=', date),
                ('location_date', '<=', date)
            ]
            attds = request.env['hr.attendance'].search(search_domain, offset = records_to_skip, limit = limit)
            total_records = request.env['hr.attendance'].search_count(search_domain)

            msg = {
                "attendances": [{
                    "check_in": convert_current_tz(current_tz, attd.check_in).strftime(TIME_FORMAT) if attd.check_in else "",
                    "check_out": convert_current_tz(current_tz, attd.check_out).strftime(TIME_FORMAT) if attd.check_out else ""
                } for attd in attds
                ] if attds else [], 
                "pagination": handle_pagination(offset, limit, total_records)
            }
            return jsonResponse(msg, 200)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

    @http.route("/api/company", type='http', auth="bearer_token", methods=["GET"])
    def company_list(self, **kw):
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if not params:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }, 400)
        try:
            offset = params["offset"]
            limit = params["limit"]
            records_to_skip = (offset - 1) * limit
            total_records = request.env['res.company'].search_count([])
            companies = request.env['res.company'].search([], offset=records_to_skip, limit=limit)
            
            response_data = {
                "companies": [
                    {
                        "id": company.id,
                        "name": company.name,
                        "email": company.email if company.email else "",
                        "phone": company.phone if company.phone else "",
                        "favicon": image_url_getter('res.company', company.id, 'favicon')
                    }
                    for company in companies
                ] if len(companies) else [],
                "pagination": handle_pagination(offset, limit, total_records)
            }
            return jsonResponse(response_data, 200)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

    @http.route("/api/employee", type='http', auth="bearer_token", methods=["GET"])
    def employee_list(self, **kw):
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if not params:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }, 400)
        try:
            offset = params["offset"]
            limit = params["limit"]
            records_to_skip = (offset- 1) * limit
            domain = []
            if kw.get('company_name'):
                domain.append(('company_id.name', 'ilike', kw['company_name']))
            if kw.get('name'):
                domain.append(('name', 'ilike', kw['name']))  
            total_records = request.env['hr.employee'].search_count(domain)
            employees = (request.env['hr.employee'].search(domain, offset=records_to_skip, limit=limit))
            
            response_data = {
                "employees": [
                    {
                        "id": employee.id,
                        "fullname": employee.name,
                        "email": employee.work_email if employee.work_email else "",
                        "phone": employee.mobile_phone if employee.mobile_phone else "",
                        "job_title": employee.job_title if employee.job_title else "", 
                        "avatar": image_url_getter('hr.employee', employee.id)
                    }
                    for employee in employees
                ] if len(employees) else [],
                "pagination": handle_pagination(offset, limit, total_records)
            }
            return jsonResponse(response_data, 200)
        except Exception as e:
            return jsonResponse({
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }, 400)

    @http.route("/api/attendance/statistic", type="http", auth="bearer_token", methods=["GET"])
    def get_attendance_statistics(self, **kwargs):
        def validate_month(month_str):
            try:
                return datetime.strptime(month_str, "%Y-%m")
            except ValueError:
                return None

        month_str = kwargs.get('month')
        month_date = validate_month(month_str)
        
        if not month_date:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Month must be in format YYYY-MM"
            }, 400)

        start_date = month_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        attendance_records = request.env['hr.attendance'].search_read(
            domain=[('location_date', '>=', start_date), ('location_date', '<=', end_date)],
            fields=['employee_id', 'location_date', 'check_in', 'check_out'],
            order='location_date asc'
        )

        date_statistics = {}
        for record in attendance_records:
            date_str = record['location_date'].strftime("%Y-%m-%d")

            if date_str not in date_statistics:
                date_statistics[date_str] = {"total_check_in": 0, "total_check_out": 0}

            if record['check_in']:
                date_statistics[date_str]["total_check_in"] += 1
            if record['check_out']:
                date_statistics[date_str]["total_check_out"] += 1

        statistics = [
            {
                "date": date_str,
                "total_check_in": data["total_check_in"],
                "total_check_out": data["total_check_out"]
            }
            for date_str, data in date_statistics.items()
        ]
        return jsonResponse({
            "status": 200,
            "data": statistics
        }, 200)

    @http.route('/api/attendance/history', auth='bearer_token', type='http', methods=['GET'])
    def get_attendance_history(self, **kwargs):
        response = check_and_handle_missing_fields(kwargs, ['employee_id', 'date'])
        if response is not None:
            return response

        employee_id = kwargs.get('employee_id')
        employee_id_int = is_valid_integer(employee_id)
        if not employee_id_int:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Employee ID must be an int"
            }, 400)
        else: 
            employee_id = int(employee_id)
        
        month_str = kwargs.get('date')
        month_date = is_valid_month(month_str)
        if not month_date:
            return jsonResponse({
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Month must be in format YYYY-MM"
            }, 400)
        
        role_check_result = self.check_role()
        if not role_check_result:
            return jsonResponse({
                    "status": 40301,
                    "message": "Forbidden",
                    "keyerror": "Access Denied"
                }, 403)

        employee = request.env['hr.employee'].search([('id', '=', employee_id)])
        if not employee:
            return jsonResponse({
                "status": 40401, 
                "message": "Not Found",
                "keyerror": "Employee not found"
            }, 404)

        start_date = month_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
        all_dates = [(start_date + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end_date - start_date).days + 1)]

        attendance_records = request.env['hr.attendance'].search_read(
            domain=[
                ('employee_id', '=', employee_id),
                ('location_date', '>=', start_date),
                ('location_date', '<=', end_date)
            ],
            fields=['location_date', 'check_in', 'check_out'],
            order='location_date asc, check_in asc'
        )

        attendance_by_date = {}
        vietnam_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
        for record in attendance_records:
            date_str = record['location_date'].strftime("%Y-%m-%d")
            day_records = attendance_by_date.setdefault(date_str, {})

            check_in = day_records.get('check_in')
            if not check_in or (record['check_in'] and record['check_in'] < check_in):
                day_records['check_in'] = record['check_in']

            check_out = day_records.get('check_out')
            if not check_out or (record['check_out'] and record['check_out'] > check_out):
                day_records['check_out'] = record['check_out']

        attendances = []

        for date in all_dates:
            record = attendance_by_date.get(date, {})
            check_in = record.get('check_in')
            check_out = record.get('check_out')

            check_in_str = check_in.replace(tzinfo=pytz.utc).astimezone(vietnam_timezone).strftime("%H:%M:%S") if check_in else ""
            check_out_str = check_out.replace(tzinfo=pytz.utc).astimezone(vietnam_timezone).strftime("%H:%M:%S") if check_out else ""
            
            duration = str(check_out - check_in) if check_in and check_out else "0:00:00"
            attendances.append({
                "date": date,
                "check_in": check_in_str,
                "check_out": check_out_str,
                "duration": duration
            })

        return jsonResponse({
            "status": 200,
            "attendances": attendances,
        }, 200)

    def check_role(self):
        current_user = request.env.user
        attendance_role = {
            "role_name": "",
            "description": ""
        }
        for permit in role_attendance:
                check_permission = current_user.has_group(f"hr_attendance.{permit.get('role_name')}")
                if check_permission:
                    attendance_role = permit

        if attendance_role['role_name'] == 'group_hr_attendance':
            employee_id = request.params.get('employee_id')
            if employee_id and int(employee_id) != current_user.employee_id.id:
                return False 

        return True