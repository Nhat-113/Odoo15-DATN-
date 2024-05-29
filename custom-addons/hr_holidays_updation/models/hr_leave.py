from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta


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
            
            
    @api.constrains('inform_to')
    def constrains_inform_to(self):
        new_follower = []
        for emp in self.inform_to.user_id.partner_id.ids:
            if emp not in self.message_follower_ids.partner_id.ids:
                new_follower.append(emp)
        if len(new_follower) > 0:
            self.message_subscribe(partner_ids=new_follower)

    def write(self, values):
        user = self.env.user
        is_officer = user.has_group('hr_holidays.group_hr_holidays_user') or self.env.is_superuser()

        if not is_officer:
            past_limit_in_day = 3
            crr_past_date_limit = fields.Date.today() - relativedelta(days=past_limit_in_day)
            if any(hol.date_from.date() < crr_past_date_limit and hol.employee_id.leave_manager_id != user for hol in self):
                raise UserError(_(f'You must have manager rights to modify/validate a time off that already begun over {past_limit_in_day} days ago.'))
        
        employee_id = values.get('employee_id', False)
        context = self.env.context

        if not context.get('leave_fast_create'):
            state = values.get('state')
            if state:
                self._check_approval_update(state)
                if any(holiday.validation_type == 'both' for holiday in self):
                    if values.get('employee_id'):
                        employees = self.env['hr.employee'].browse(values.get('employee_id'))
                    else:
                        employees = self.mapped('employee_id')
                    self._check_double_validation_rules(employees, state)
            if 'date_from' in values:
                values['request_date_from'] = values['date_from']
            if 'date_to' in values:
                values['request_date_to'] = values['date_to']

        result = super(HrLeave, self).write(values)
        if employee_id and not context.get('leave_fast_create'):
            for holiday in self:
                holiday.add_follower(employee_id)
        return result
        