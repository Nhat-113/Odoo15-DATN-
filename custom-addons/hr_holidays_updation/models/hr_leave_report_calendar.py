from odoo import models, fields, api

class HrLeaveReportCalendar(models.Model):
    _inherit = 'hr.leave.report.calendar'
    
    employee_id_public = fields.Many2one('hr.employee.public', string='Employee', compute='_compute_employee_id_public')
    
    @api.depends('employee_id')
    def _compute_employee_id_public(self):
        employee_ids = self.mapped('employee_id.id')
        
        public_employees = self.env['hr.employee.public'].search([('id', 'in', employee_ids)])
        public_employee_map = {pub_emp.employee_id.id: pub_emp for pub_emp in public_employees}
        
        for record in self:
            record.employee_id_public = public_employee_map.get(record.employee_id.id, record.employee_id)