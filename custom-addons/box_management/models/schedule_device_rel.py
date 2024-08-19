# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScheduleDeviceRel(models.Model):
    _name = "schedule.device.rel"
    _description = "Schedule For Facelog Device Relation"

    schedule_id = fields.Many2one('setting.device')
    device_id = fields.Char()
    active = fields.Boolean()
    