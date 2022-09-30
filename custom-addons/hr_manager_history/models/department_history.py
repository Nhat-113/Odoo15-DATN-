from odoo import models, fields, api


class HrEmployeeDepartmentHistory(models.Model):
    _name = 'hr.department.history'
    _order = 'id desc'

    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    date_start = fields.Datetime('Create Manager date', readonly=True)
    date_end = fields.Datetime('Change Manager date', readonly=True)
    manager_history_id = fields.Many2one('hr.employee', string='Manager history')  

