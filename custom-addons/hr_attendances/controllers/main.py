# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta 
from odoo.addons.web.controllers.main import Session

import datetime


class HrAttendance(http.Controller):
    @http.route('/api/facelog_attendances',auth='api_key', type='json')
    def facelog_attendances(self, **kw):
        # Fixme: get config domain email with comapy
        email = kw['nick_name'] + '@d-soft.com.vn'
        employees = request.env['hr.employee'].search([('work_email','=',email)])
        if len(employees):
            # convert string to datetime
            try:
                date_time = datetime.datetime.strptime(kw['date_time'], "%m/%d/%Y, %H:%M:%S")
            except:
                return {"status":500, "Message": "Value input does not match format '%m/%d/%Y, %H:%M:%S"}
            # convert local+7 to UTC+0
            date_time = date_time - timedelta(hours = 7)
            if kw['is_checkin']=='True' or kw['is_checkin']=='False':
                result = request.env['hr.employee'].attendance_manual_api(employees, date_time, "hr_attendance.hr_attendance_action_my_attendances", kw['is_checkin'])
            else: 
                return {"status":404, "message":"missing is_checkin param or value does not match fomat bool"}
            
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
            email = kw['nick_name'] + '@d-soft.com.vn'
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
            if not kw["nick_name"]:
                return {"status": 404, "message": "Missing nick_name parameter"}
            else:
                return {"status": 400, "massage": "Bad requests"}

class SessionCustom(Session):
    @http.route('/web/session/authenticate/api_attendances_key', type='json', auth='public', sitemap=False)
    def authenticate(self, uid):
        try:
            api_key = request.env['auth.api.key'].search([('user_id','=',uid)], limit=1).key
        except:
            api_key = None
        
        try:
            value = {"status": 200, "value": {"message": "Connect Success", "api_key": api_key}}
            return value
        except:
            return {"status": 400, "message":"Bad request"}