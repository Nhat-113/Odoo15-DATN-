# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta 
from odoo.addons.web.controllers.main import Session

import datetime


class HrAttendance(http.Controller):
    @http.route('/api/facelog/attendance_odoo',auth='api_key', type='json')
    def facelog_attendances(self, **kw):
        if kw['is_checkin']=="" or kw['date_time']=="" or kw['email']=="":
            return {
                "status": 400, 
                "message": "Missing parameter"
                }
        else:
            # Fixme: get config domain email with comapy
            # email = kw['nick_name'] + '@d-soft.com.vn'
            email = kw['email']
            employees = request.env['hr.employee'].search([('work_email','=',email)])
            if len(employees):
                # convert string to datetime
                try:
                    date_time = datetime.datetime.strptime(kw['date_time'], "%m/%d/%Y, %H:%M:%S")
                except:
                    return {"status": 500, "Message": "Value input does not match format '%m/%d/%Y, %H:%M:%S"}
                # convert local+7 to UTC+0
                date_time = date_time - timedelta(hours = 7)
                
                if kw['is_checkin']=='True' or kw['is_checkin']=='False':
                    """ verifies if check_in is earlier than check_out. """
                    if employees.attendance_ids:
                        attendance = employees.attendance_ids[employees.attendance_ids.ids.index(max(employees.attendance_ids.ids))]
                        if attendance.check_in and date_time < attendance.check_in and kw['is_checkin']=='False':
                            return {"status": 402, "message": "'Check Out' cannot be earlier than 'Check In'"}
                                 
                    result = request.env['hr.employee'].attendance_manual_api(employees, date_time, "hr_attendance.hr_attendance_action_my_attendances", kw['is_checkin'])  
                else: 
                    return {"status": 404, "message": "is_checkin param does not match format boolean"}
                
                response_message = result['action']['attendance']
                response = {
                    "id": response_message['id'],
                    "employee_id": response_message['employee_id'],
                    "check_in": response_message['check_in'],
                    "check_out": response_message['check_out'],
                    "worked_hours": response_message['worked_hours']
                }
                return {"status": 200, "message": response}
            else:
                return  {"status": 400, "message": "User does not exist"}


    @http.route('/api/attendances/getuser', auth='api_key', type='json')
    def facelog_getuser(self, **kw):
        try:
            # email = kw['nick_name'] + '@d-soft.com.vn'
            email = kw['email']
            employee = request.env['hr.employee'].search([('work_email','=',email)])
            if not employee:
                return {"status": 400, "message": "User does not exits"}
            response = {
                "status": 200, 
                "message": "Request success", 
                "values": 
                    {
                        "full_name": employee.name,
                        "birth_day": employee.birthday
                    }
                }
            return response
        except:
            if not kw["email"] and not kw:
                return {"status": 404, "message": "Missing email parameter"}
            else:
                return {"status": 400, "massage": "Missing parameter"}

    @http.route('/api/attendances/get_public_holiday', auth='public', type='json')
    def facelog_get_public_holiday(self, **kw):
        try:
            if kw:
                return {
                    "status": 400,
                    "massage": "No need any parameters",
                }
            else:
                vals = []
                public_holiday = request.env['resource.calendar.leaves'].search([('resource_id','=',False),('holiday_id','=',False)])
                for record in public_holiday:
                    holiday = {
                                'item': record.name,
                                'date_from': record.date_from + timedelta(hours = 7),
                                'date_to': record.date_to + timedelta(hours = 7)
                                }
                    vals.append(holiday)

                return {
                    "status": 200,
                    "message": "Request success",
                    "values": vals
                }
        except:
            return {
                    "status": 500,
                    "massage": "Odoo Server Error",
                }


class SessionCustom(Session):
    @http.route('/web/session/authenticate/api_attendances_key', type='json', auth='public', sitemap=False)
    def authenticate(self, **uid):
        try:
            if uid:
                user = request.env['auth.api.key'].search([('user_id','=',uid["uid"])], limit=1)
                api_key = user.key
            else:
                return {"status": 404, "message": "Missing uid parameter"}
        except:
            api_key = None
        
        if api_key:
            value = {
                "status": 200, 
                "value": {
                    "message": "Connect Success", 
                    "api_key": api_key,
                    "user": user.user_id.display_name
                    }
                }
            return value
        else: 
            return {"status": 400, "message": "Nothing api key mapping with uid parameter"}