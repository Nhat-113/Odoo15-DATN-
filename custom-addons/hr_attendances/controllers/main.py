# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from urllib import response
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta 
import datetime
import json

class HrAttendance(http.Controller):
    @http.route('/api/facelog_attendances',auth='api_key', type='json')
    def facelog_attendances(self, **kw):
        # Fixme: get config domain email with comapy
        email = kw['nick_name'] + '@d-soft.com.vn'
        employees = request.env['hr.employee'].search([('work_email','=',email)])
        if len(employees):
            # convert string to datetime
            date_time = datetime.datetime.strptime(kw['date_time'], "%m/%d/%Y, %H:%M:%S")
            # convert local+7 to UTC+0
            date_time = date_time - timedelta(hours = 7)
            result = request.env['hr.employee'].attendance_manual_api(employees, date_time, "hr_attendance.hr_attendance_action_my_attendances")
            response_message = result['action']['attendance']
            return response_message
        else:
            return  "User does not exist"
