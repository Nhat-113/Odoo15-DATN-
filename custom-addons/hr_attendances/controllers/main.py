# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from urllib import response
from odoo import http
from odoo.http import request


class HrAttendance(http.Controller):
    @http.route('/facelog_attendances', auth='user', type='json')
    def facelog_attendances(self, **kw):
        print('--check api---')
        employee = request.env['hr.employee'].search([('id','=',kw['employee_id'])])
        request.env['hr.employee'].attendance_manual_api(employee, kw['next_action'])
        return {'200 Suscess'}