# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BoxEmployeeRel(models.Model):
    _name = "box.employee.rel"
    _description = "Box Employee Relation"

    device_id = fields.Many2one('box.management')
    employee_id = fields.Many2one('hr.employee')
    delete_at = fields.Datetime()
    