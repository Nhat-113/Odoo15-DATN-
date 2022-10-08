from odoo import models, fields, api


class HrEmployeeDepartmentHistory(models.Model):
    _name = 'hr.department.history'
    _order = 'id desc'

    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    date_start = fields.Date('Date Start')
    date_end = fields.Date('Date End')
    manager_history_id = fields.Many2one('hr.employee', string='Manager history')  

