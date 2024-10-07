from odoo import http
from datetime import datetime, timedelta
from odoo.http import request
from dateutil.relativedelta import relativedelta
# from odoo.tools import  config
import pytz
from helper.helper import message_error_missing, check_field_missing_api, jsonResponse, convert_current_tz, check_authorize, handle_pagination, validate_pagination, image_url_getter, is_valid_month, is_valid_integer, check_and_handle_missing_fields, mobile_error_response
from helper.hr_employee_common import get_all_department_children
import logging

_logger = logging.getLogger(__name__)
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
            log_data = {'GET': '/api/me'}
            user = request.env.user
            employee = request.env.user.employee_id
            
            attendance_role = {
                "role_name": "",
                "description": ""
            }
            for permit in role_attendance:
                check_permission = user.has_group(f"hr_attendance.{permit.get('role_name')}")
                if check_permission:
                    attendance_role = permit

            data = {
                "avatar": self.get_avatar_model('hr.employee', employee.id) if employee else None,
                "role": attendance_role,
                "employee_id": employee.id if employee else None
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

            res = {
                "status": 200,
                "data": data,
            }
            _logger.info({**log_data, **res})
            return jsonResponse({"data": res["data"]}, res["status"])
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_info(self, employee_id, **kwargs):
        try:
            log_data = {"GET": f'/api/employee/{employee_id}'}
            user = request.env.user
            request_user_id = request.uid
            if not check_authorize('hr.employee', request_user_id):
                employee = request.env['hr.employee.public'].search([('id', '=', employee_id)])
            else:
                employee = request.env['hr.employee'].search([('id', '=', employee_id)])

            if not employee:
                res = {
                    "status": 40401,
                    "message": "Not found",
                    "keyerror": "Employee Not Found"
                }
                _logger.info({**log_data, **res})
                return jsonResponse(res, 404)
            
            data = { "avatar": self.get_avatar_model('hr.employee', employee_id) }
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
            
            res = {'status': 200, "data": data}
            _logger.info({**log_data, **res})
            return jsonResponse({"data": res["data"]}, res["status"])
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/attendance/employee", type="http", auth="bearer_token", methods=["GET"])
    def get_attendance_data(self, **kwargs):
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        log_data = {**{'GET': '/api/attendance/employee'}, **kwargs}
        if not params:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
        try:
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                res = {
                    "status": 40301,
                    "message": "Forbidden",
                    "keyerror": "Access Denied"
                }
                _logger.info({**log_data, **res})
                return jsonResponse(res, 403)
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                res = {
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": message_error_missing(missing_fields)
                }
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)
            
            
            date_str = kwargs.get('date')
            date = datetime.strptime(date_str, "%Y-%m-%d")
            name = kwargs.get('name')
            company_name = kwargs.get('company_name')
            company_ids = kwargs.get('company_ids')
            type = kwargs.get('type', 'all')
            offset = params["offset"]
            limit = params["limit"]
            records_to_skip = (offset - 1) * limit
            
            search_domain = [('location_date', '=', date)]

            if name:
                search_domain.append(('employee_id.name', 'ilike', name))
            if company_name:
                search_domain.append(('employee_id.company_id.name', 'ilike', company_name))

            if company_ids:
                company_ids_list = company_ids.split(',')
                company_ids_int = all(is_valid_integer(company_id) for company_id in company_ids_list)
                if not company_ids_int:
                    res = {
                        "status": 40001,
                        "message": "Invalid",
                        "keyerror": "Company ID must be an int"
                    }
                    _logger.info({**log_data, **res})
                    return jsonResponse(res, 400)
                search_domain.append(('employee_id.company_id.id', 'in', company_ids_list))

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

            is_multiple_mode = request.env.user.employee_id.company_id.attendance_view_type
            durations = {}
            if is_multiple_mode:
                all_attds = request.env['hr.attendance'].search(
                    args=search_domain,
                    offset=records_to_skip,
                    limit=limit
                )
                for attd in all_attds:
                    emp_id = attd.employee_id.id
                    if attd.check_in and attd.check_out:
                        duration_seconds = attd.check_out - attd.check_in
                        if emp_id in durations:
                            durations[emp_id] += duration_seconds
                        else:
                            durations[emp_id] = duration_seconds
                    else: 
                        if emp_id not in durations:
                            durations[emp_id] = timedelta(0)

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
                        "avatar": self.get_avatar_model('hr.employee', employee["id"]),
                    } 
                    first_check_in = convert_current_tz(current_tz, attd[0]['check_in']).strftime(TIME_FORMAT) if attd[0]['check_in'] else ""
                    last_check_out = convert_current_tz(current_tz, attd[0]['check_out']).strftime(TIME_FORMAT) if attd[0]['check_out'] else ""
                    if type == 'checkin':
                        entry["check_in"] = first_check_in
                    elif type == 'checkout':
                        entry["check_out"] = last_check_out
                    else: 
                        entry["check_in"] = first_check_in
                        entry["check_out"] = last_check_out

                    entry["duration"] = timedelta(0)
                    if is_multiple_mode:
                        entry["duration"] = durations[entry["employee_id"]]
                    else:
                        if first_check_in and last_check_out and attd[0]['check_out'] >= attd[0]['check_in']:
                            entry["duration"] = attd[0]['check_out'] - attd[0]['check_in']
                    attendances.append(entry)

            res = {
                "attendances": attendances,
                "pagination": handle_pagination(offset, limit, total_records)
            }
            _logger.info({**log_data, **{'status': 200}, **res})
            return jsonResponse(res, 200)  
        
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/attendance/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_attendances(self, employee_id, **kwargs):
        log_data = {**{'GET': f'/api/attendance/employee/{employee_id}'}, **kwargs}
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        if not params:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
        try:
            current_tz = request.env.user.tz
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                res = {
                    "status": 403,
                    "message": "Access Denied",
                }
                _logger.info({**log_data, **res})
                return jsonResponse({"message": res["message"]}, res["status"])
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                res = {
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": message_error_missing(missing_fields)
                }
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)
            
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
            _logger.info({**log_data, **{'status': 200}, **msg})
            return jsonResponse(msg, 200)
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/company", type='http', auth="bearer_token", methods=["GET"])
    def company_list(self, **kw):
        log_data = {**{'GET': '/api/company'}, **kw}
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if not params:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
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
                        "favicon": self.get_avatar_model('res.company', company.id)
                    }
                    for company in companies
                ] if len(companies) else [],
                "pagination": handle_pagination(offset, limit, total_records)
            }
            _logger.info({**log_data, **{'status': 200}, **res})
            return jsonResponse(response_data, 200)
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/employee", type='http', auth="bearer_token", methods=["GET"])
    def employee_list(self, **kw):
        log_data = {**{'GET': '/api/employee'}, **kw}
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if not params:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Page or Per_page must be an integer number"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
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
                        "avatar": self.get_avatar_model('hr.employee', employee.id)
                    }
                    for employee in employees
                ] if len(employees) else [],
                "pagination": handle_pagination(offset, limit, total_records)
            }
            _logger.info({**log_data, **{'status': 200}, **response_data})
            return jsonResponse(response_data, 200)
        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": e
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

    @http.route("/api/attendance/statistic", type="http", auth="bearer_token", methods=["GET"])
    def get_attendance_statistics(self, **kwargs):
        log_data = {**{'GET': '/api/attendance/statistic'}, **kwargs}
        missing_fields = check_field_missing_api(kwargs, ['month'])
        if len(missing_fields) > 0:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": message_error_missing(missing_fields)
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

        def validate_month(month_str):
            try:
                return datetime.strptime(month_str, "%Y-%m")
            except ValueError:
                return None

        company_ids = kwargs.get('company_ids')
        month_str = kwargs.get('month')
        month_date = validate_month(month_str)
        
        if not month_date:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Month must be in format YYYY-MM"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)

        start_date = month_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

        search_domain = [
            ('location_date', '>=', start_date), 
            ('location_date', '<=', end_date)
        ]
        
        if company_ids:
            company_ids_list = company_ids.split(',')
            company_ids_int = all(is_valid_integer(company_id) for company_id in company_ids_list)
            if not company_ids_int:
                res = {
                    "status": 40001,
                    "message": "Invalid",
                    "keyerror": "Company ID must be an int"
                }
                _logger.info({**log_data, **res})
                return jsonResponse(res, 400)
            search_domain.append(('employee_id.company_id.id', 'in', company_ids_list))

        attendance_records = request.env['hr.attendance'].read_group(
            groupby=['location_date:day', 'employee_id'],
            fields=['check_in:min', 'check_out:max'],
            domain=search_domain,
            lazy=False
        )

        date_statistics = {}
        for record in attendance_records:
            date_obj = datetime.strptime(record['location_date:day'], '%d %b %Y')
            date_str = date_obj.strftime("%Y-%m-%d")

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
        res = {
            "status": 200,
            "data": statistics
        }
        _logger.info({**log_data, **res})
        return jsonResponse(res, 200)

    @http.route('/api/attendance/history', auth='bearer_token', type='http', methods=['GET'])
    def get_attendance_history(self, **kwargs):
        log_data = {**{'GET': '/api/attendance/history'}, **kwargs}
        response = check_and_handle_missing_fields(kwargs, ['employee_id', 'date'])
        if response is not None:
            return response

        employee_id = kwargs.get('employee_id')
        employee_id_int = is_valid_integer(employee_id)
        if not employee_id_int:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Employee ID must be an int"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
        else: 
            employee_id = int(employee_id)
        
        month_str = kwargs.get('date')
        month_date = is_valid_month(month_str)
        if not month_date:
            res = {
                "status": 40001,
                "message": "Invalid",
                "keyerror": "Month must be in format YYYY-MM"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)
        
        role_check_result = self.check_role()
        direct_subordinates_result = self.is_employee_in_department(employee_id)
        if not role_check_result and not direct_subordinates_result:
            res = {
                "status": 40301,
                "message": "Forbidden",
                "keyerror": "Access Denied"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 403)

        employee = request.env['hr.employee'].search([('id', '=', employee_id)])
        if not employee:
            res = {
                "status": 40401, 
                "message": "Not Found",
                "keyerror": "Employee not found"
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 404)

        start_date = month_date.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
        all_dates = [(start_date + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end_date - start_date).days + 1)]

        domain = [
            ('employee_id', '=', employee_id),
            ('location_date', '>=', start_date),
            ('location_date', '<=', end_date)
        ]

        attendance_records = request.env['hr.attendance'].sudo().search_read(
            domain=domain,
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

        is_multiple_mode = request.env.user.employee_id.company_id.attendance_view_type
        durations = {}
        if is_multiple_mode:
            all_attds = request.env['hr.attendance'].search(domain)
            for attd in all_attds:
                date = attd.location_date.strftime("%Y-%m-%d")
                if attd.check_in and attd.check_out:
                    duration_seconds = attd.check_out - attd.check_in
                    if date in durations:
                        durations[date] += duration_seconds
                    else:
                        durations[date] = duration_seconds
                else: 
                    if date not in durations:
                        durations[date] = timedelta(0)

        attendances = []

        for date in all_dates:
            record = attendance_by_date.get(date, {})
            check_in = record.get('check_in')
            check_out = record.get('check_out')

            check_in_str = check_in.replace(tzinfo=pytz.utc).astimezone(vietnam_timezone).strftime("%H:%M:%S") if check_in else ""
            check_out_str = check_out.replace(tzinfo=pytz.utc).astimezone(vietnam_timezone).strftime("%H:%M:%S") if check_out else ""
            
            duration = timedelta(0)
            if is_multiple_mode:
                duration = durations[date] if date in durations else timedelta(0)
            else:
                if check_in_str and check_out_str and check_out >= check_in:
                    duration = check_out - check_in

            attendances.append({
                "date": date,
                "check_in": check_in_str,
                "check_out": check_out_str,
                "duration": duration
            })
        res = {
            "status": 200,
            "attendances": attendances,
        }
        _logger.info({**log_data, **res})
        return jsonResponse(res, 200)
    # handle for department role emp
    def is_employee_in_department(self, employee_id):
        current_user_id = request.env.user.employee_id.id
        if not current_user_id:
            return False

        current_department = request.env['hr.department'].search([('manager_id', '=', current_user_id)])
        if not current_department:
            return False

        all_departments = request.env['hr.department'].search([('id', 'child_of', current_department.ids)])

        all_employees_in_departments = request.env['hr.employee'].search([('department_id', 'in', all_departments.ids)])

        return employee_id in all_employees_in_departments.ids

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
    
    def get_avatar_model(self, model, id):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        avatar = f"{base_url}/api/get_image?model={model}&id={id}"
        
        return avatar
    
    @http.route('/api/get_image', type='http', auth="bearer_token", website=True, sitemap=False)
    def mobile_get_image(self, **kwargs):
        log_data = {**{http.request.httprequest.method: '/api/get_image'}, **kwargs}
        model = kwargs.get('model')
        id = kwargs.get('id')
        
        field = 'logo' if model == 'res.company' else 'image_1920'
        status, headers, image_base64 = request.env['ir.http'].sudo().binary_content(
            model=model,
            id=id,
            field=field,
            default_mimetype='image/png'
        )
        result = request.env['ir.http']._content_image_get_response(status, headers, image_base64)

        _logger.info(log_data)
        return result

    @http.route("/api/manager/members", type='http', auth="bearer_token", methods=["GET"])
    def member_list(self, **kw):
        log_data = {**{'GET': '/api/manager/members'}, **kw}
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if not params:
            _logger.info({**log_data, **{
                'status': 40001,
                'message': 'Invalid',
                'keyerror': 'Page or Per_page must be an integer number'
            }})
            return mobile_error_response(status=40001, message="Invalid", keyerror_message="Page or Per_page must be an integer number")

        missing_fields = check_field_missing_api(kw, ['employee_id'])
        if missing_fields:
            keyerror_message = message_error_missing(missing_fields)
            _logger.info({**log_data, **{
                'status': 40001,
                'message': 'Invalid',
                'keyerror': keyerror_message
            }})
            return mobile_error_response(status=40001, message="Invalid", keyerror_message=keyerror_message)

        employee_id = kw.get("employee_id")
        if not employee_id.isdigit() or int(employee_id) == 0:
            _logger.info({**log_data, **{
                'status': 40001,
                'message': 'Invalid',
                'keyerror': 'The member_id must be a positive integer'
            }})
            return mobile_error_response(status=40001, message="Invalid", keyerror_message="The member_id must be a positive integer")

        try:
            departments = request.env['hr.department'].search([('manager_id.id', '=', employee_id)]).ids
            if not departments:
                _logger.info({**log_data, **{
                    'status': 40001,
                    'message': 'Invalid',
                    'keyerror': 'The current user is not a manager.'
                }})
                return mobile_error_response(status=40001, message="Invalid", keyerror_message="The current user is not a manager.")

            departments.extend(get_all_department_children(request=request, parent_id=departments, list_departments=[]))
            domain = [('department_id.id', 'in', departments), ('id', '!=', employee_id)]
            
            if kw.get('name'):
                domain.append(('name', 'ilike', kw['name']))

            offset, limit = params["offset"], params["limit"]
            records_to_skip = (offset - 1) * limit
            total_records = request.env['hr.employee'].search_count(domain)
            employees = request.env['hr.employee'].search(domain, offset=records_to_skip, limit=limit)

            response_data = {
                "employees": [
                    {
                        "id": employee.id,
                        "fullname": employee.name,
                        "email": employee.work_email or "",
                        "phone": employee.mobile_phone or "",
                        "job_title": employee.job_title or "",
                        "avatar": self.get_avatar_model('hr.employee', employee.id)
                    }
                    for employee in employees
                ],
                "pagination": handle_pagination(offset, limit, total_records)
            }
            _logger.info({**log_data, **{'status': 200}, **response_data})
            return jsonResponse(response_data, 200)

        except Exception as e:
            res = {
                "status": 40002,
                "message": "Bad request",
                "keyerror": str(e)
            }
            _logger.info({**log_data, **res})
            return jsonResponse(res, 400)