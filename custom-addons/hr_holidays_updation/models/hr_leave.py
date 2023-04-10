from odoo import models, fields


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    
    inform_to = fields.Many2many('hr.employee', 'hr_leave_employee_inform_rel', 'hr_leave_id', 'employee_id', store=True, string="Inform to")


    ####################################################
    # Overrides methods
    ####################################################    
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        followers = employee.user_id.partner_id.ids + self.inform_to.user_id.partner_id.ids
        if employee.user_id:
            self.message_subscribe(partner_ids=followers)