# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta 
import datetime
from odoo.addons.web.controllers.main import Session

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
                return {"Status":"500 Internal Server Error","Message": "Value input does not match format '%m/%d/%Y, %H:%M:%S"}
            # convert local+7 to UTC+0
            date_time = date_time - timedelta(hours = 7)
            result = request.env['hr.employee'].attendance_manual_api(employees, date_time, "hr_attendance.hr_attendance_action_my_attendances", kw['is_checkin'])
            response_message = result['action']['attendance']

            response = {
                "id":response_message['id'],
                "employee_id": response_message['employee_id'],
                "check_in": response_message['check_in'],
                "check_out": response_message['check_out'],
                "worked_hours": response_message['worked_hours']
            }


            return {"status": "200 success", "message":response}
        else:
            return  {"status": "200 success", "message": "User does not exist"}

class SessionCustom(Session):
    @http.route('/web/session/authenticate/api_attendances_key', type='json', auth='public', sitemap=False)
    def authenticate(self, uid):
        try:
            api_key = request.env['auth.api.key'].search([('user_id','=',uid)], limit=1).key
        except:
            api_key = None
        value = {"status": "200 success", "value": {"message": "Connect Success", "api_key": api_key}}
        return value