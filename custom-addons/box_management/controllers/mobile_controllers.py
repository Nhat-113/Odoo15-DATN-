from odoo import http
from datetime import datetime
from odoo.http import request
# from odoo.tools import  config
from helper.helper import message_error_missing, check_field_missing_api, jsonResponse, convert_current_tz, check_authorize, handle_pagination, validate_pagination, image_url_getter

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
            current_user = request.env["res.users"].browse(request.uid)
            employee_id = current_user.employee_id if current_user.employee_id else None
            company = getattr(employee_id, 'company_id', None)
            department = getattr(employee_id, 'department_id', None)
            job = getattr(employee_id, 'job_id', None)
            manager = getattr(employee_id, 'parent_id', None)
            coach = getattr(employee_id, 'coach_id', None)
            attendance_role = {
                "role_name": "",
                "description": ""
            }
            for permit in role_attendance:
                check_permission = request.env.user.has_group(f"hr_attendance.{permit.get('role_name')}")
                if check_permission:
                    attendance_role = permit
            return jsonResponse(
                {
                    "data": {
                        "id": current_user["id"],
                        "fullname": current_user["display_name"],
                        "email": current_user["email"] if current_user["email"] else "",
                        "phone": current_user["phone"] if current_user["phone"] else "",
                        "avatar": image_url_getter('res.user', request.uid),
                        "role": attendance_role,
                        "company": {
                            "id": employee_id.company_id.id,
                            "name": employee_id.company_id.name 
                        } if company else None,
                        "department": {
                            "id": employee_id.department_id.id,
                            "name": employee_id.department_id.name
                        } if department else None,
                        "job": {
                            "id": employee_id.job_id.id,
                            "name": employee_id.job_id.name
                        } if job else None,
                        "manager": {
                            "id": employee_id.parent_id.id,
                            "name": employee_id.parent_id.name
                        } if manager else None,
                        "coach": {
                            "id": employee_id.coach_id.id,
                            "name": employee_id.coach_id.name
                        } if coach else None,
                    }
                }, 200)
        except Exception as e:
            return jsonResponse({"message": f"Error unexpected: {e}"}, 400)

    @http.route("/api/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_info(self, employee_id, **kwargs):
        try:
            request_user_id = request.uid
            if not check_authorize('hr.employee', request_user_id):
                return jsonResponse({"message": "Access Denied"}, 403)
            
            employee = request.env['hr.employee'].search([('id', '=', employee_id)])
            
            msg = {
                "data": {
                    "id": employee.id,
                    "fullname": employee.name,
                    "phone": employee.work_phone if employee.work_phone else "",
                    "email": employee.work_email if employee.work_email else "",
                    "avatar": image_url_getter('hr.employee', employee.id),
                    "company": {
                        "id": employee.company_id.id,
                        "name": employee.company_id.name 
                    } if employee.company_id else None,
                    "department": {
                        "id": employee.department_id.id,
                        "name": employee.department_id.name
                    } if employee.department_id else None,
                    "job": {
                        "id": employee.job_id.id,
                        "name": employee.job_id.name
                    } if employee.job_id else None,
                    "manager": {
                        "id": employee.parent_id.id,
                        "name": employee.parent_id.name
                    } if employee.parent_id else None,
                    "coach": {
                        "id": employee.coach_id.id,
                        "name": employee.coach_id.name
                    } if employee.coach_id else None,
                    # "address": employee.address_id.id
                } if employee else None
            }
            return jsonResponse(msg, 200)
        except Exception as e:
            return jsonResponse({"message": f"Bad request: {e}"}, 400)

    @http.route("/api/attendance/employee", type="http", auth="bearer_token", methods=["GET"])
    def get_attendance_data(self, **kwargs):
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        if params is False:
            return jsonResponse({"message": "Page or Per_page must be an integer number"}, 400)
        try:
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                return jsonResponse({"message": "Access Denied"}, 403)
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                return jsonResponse({"message": message_error_missing(missing_fields)}, 400)
            
            
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
            return jsonResponse({"message": f"Bad request: {e}"}, 400)

    @http.route("/api/attendance/employee/<int:employee_id>", type="http", auth="bearer_token", methods=["GET"])
    def get_employee_attendances(self, employee_id, **kwargs):
        params = validate_pagination(kwargs.get('page', 1), kwargs.get('per_page', 10))
        if params is False:
            return jsonResponse({"message": "Page or Per_page must be an integer number"}, 400)
        try:
            current_tz = request.env.user.tz
            request_user_id = request.uid
            if not check_authorize('hr.attendance', request_user_id):
                return jsonResponse({"message": "Access Denied"}, 403)
            
            missing_fields = check_field_missing_api(kwargs, ['date'])
            if 'date' in missing_fields:
                return jsonResponse({"message": message_error_missing(missing_fields)}, 400)
            
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
            return jsonResponse({"message": f"Bad request: {e}"}, 400)

    @http.route("/api/company", type='http', auth="bearer_token", methods=["GET"])
    def company_list(self, **kw):
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if params is False:
            return jsonResponse({"message": "Page or Per_page must be an integer number"}, 400)
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
            return jsonResponse({"message": f"Error unexpected: {e}"}, 400)

    @http.route("/api/employee", type='http', auth="bearer_token", methods=["GET"])
    def employee_list(self, **kw):
        params = validate_pagination(kw.get('page', 1), kw.get('per_page', 10))
        if params is False:
            return jsonResponse({"message": "Page or Per_page must be an integer number"}, 400)
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
            return jsonResponse({"message": f"Error unexpected: {e}"}, 400)
