from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta

PAST_LIMIT_IN_DAY = 3

class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    inform_to = fields.Many2many('hr.employee', 'hr_leave_employee_inform_rel', 'hr_leave_id', 'employee_id', store=True, string="Inform to")
    new_inform_to = fields.Many2many('hr.employee', 'hr_leave_employee_inform_rel', 'hr_leave_id', 'employee_id', string="New inform to")
    extra_approvers = fields.Many2many('hr.employee', 'hr_leave_employee_extra_approvers_rel', 'hr_leave_id', 'employee_id',
                            string="Extra Approvers", compute="_compute_extra_approvers", store=True, readonly=True)
    
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
        if 'inform_to' in values:
            self.write_send_mail(values)
        user = self.env.user
        is_officer = user.has_group('hr_holidays.group_hr_holidays_user') or self.env.is_superuser()

        if not is_officer:
            crr_past_date_limit = fields.Date.today() - relativedelta(days=PAST_LIMIT_IN_DAY)
            if any(hol.date_from.date() < crr_past_date_limit and hol.employee_id.leave_manager_id != user for hol in self):
                raise UserError(_(f'You must have manager rights to modify/validate a time off that already begun over {PAST_LIMIT_IN_DAY} days ago.'))
            
            leaves = self._get_leaves_on_public_holiday()
            if leaves:
                employee_names = ', '.join(leaves.mapped('employee_id.name'))
                raise UserError(_('These employees: %s are not supposed to work during that period.') % employee_names)
        
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
                
        # Model hr.leave inherit mail.thread
        # which mean: in hr.leave write method, super(HolidayRequest, self).write(values) call mail.thread's write method
        # So, in this case, where we completely override the whole write method
        # we need to call mail.thread's write method to keep the original behaviour
        result = super(type(self.env['mail.thread']), self).write(values)
        if employee_id and not context.get('leave_fast_create'):
            for holiday in self:
                holiday.add_follower(employee_id)
        return result
    
    @api.ondelete(at_uninstall=False)
    def _unlink_if_correct_states(self):
        error_message = _('You cannot delete a time off which is in %s state')
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        
        if not self.user_has_groups('hr_holidays.group_hr_holidays_user'):
            if any(hol.state not in ['draft', 'confirm'] for hol in self):
                raise UserError(error_message % state_description_values.get(self[:1].state))
        else:
            for holiday in self.filtered(lambda holiday: holiday.state not in ['draft', 'cancel', 'confirm']):
                raise UserError(error_message % (state_description_values.get(holiday.state),))

    @api.depends('date_from', 'date_to')
    def _compute_extra_approvers(self):
        now = fields.Datetime.now()
        user_company = self.env.user.company_id
        
        running_projects = self.env['project.project'].search([
            ('date_start', '<=', now),
            ('date', '>=', now)
        ])
        
        pm_ids = [
            project.user_id.employee_id.id 
            for project in running_projects
            if project.user_id.company_id == user_company
            and project.user_id != self.env.user.leave_manager_id
            and project.user_id != self.env.user
            and project.user_id.employee_id
        ]
        
        for leave in self:
            leave.extra_approvers = [(6, 0, pm_ids)]

    @api.onchange('extra_approvers')
    def _inform_to_extra_approvers(self):
        for leave in self:
            leave.inform_to = [(6, 0, leave.extra_approvers.ids)]

    def _is_an_extra_approvers(self):
        return self.env.user.employee_id in self.extra_approvers
    
    @api.depends_context('uid')
    def _compute_description(self):
        super(HrLeave, self)._compute_description()
        for leave in self:
            if leave._is_an_extra_approvers():
                leave.name = leave.sudo().private_name

    @api.ondelete(at_uninstall=False)
    def _check_unlink_rights(self):
        crr_user = self.env.user
        is_timeoff_officer = crr_user.has_group('hr_holidays.group_hr_holidays_user')
        is_timeoff_manager = crr_user.has_group('hr_holidays.group_hr_holidays_manager')
        for leave in self:
            if  leave.state in ['draft', 'confirm'] and not (is_timeoff_manager or is_timeoff_officer or (leave.employee_id == crr_user.employee_id)):
                raise UserError('Only the employee who requested the Timeoff or a Timeoff Officer/Administrator can delete a timeoff request.')
            
    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrLeave, self).create(vals_list)
        new_follower = []
        for emp in records.inform_to:
            if emp not in records.message_follower_ids.partner_id.ids:
                new_follower.append(emp.work_email)

        if len(new_follower) > 0: 
            records.new_inform_to = records.inform_to # Update Many2many field with new inform to
            records.send_mail_to_inform()
        return records
    
    def send_mail_to_inform(self):
        template_id = 'hr_holidays_updation.template_send_mail_inform_to'
        template = self.env.ref(template_id, raise_if_not_found=False)
        template.send_mail(self.id, force_send=True)

    def write_send_mail(self, vals_list):
        new_follower = []
        for emp in vals_list['inform_to'][0][2]:
            if emp not in self.message_follower_ids.partner_id.ids and emp not in self.inform_to.ids:
                new_follower.append(emp)
        if len(new_follower) > 0:
            self.new_inform_to = [(6, 0, new_follower)] # Update Many2many field with new inform to
            self.send_mail_to_inform()    