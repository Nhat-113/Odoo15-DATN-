from odoo import models, fields, api, tools
from odoo.exceptions import UserError
from odoo.tools.translate import _
from dateutil.relativedelta import relativedelta

class HrLeave(models.Model):
    _inherit = 'hr.leave'
    
    inform_to = fields.Many2many('hr.employee', 'hr_leave_employee_inform_rel', 'hr_leave_id', 'employee_id', store=True, string="Inform to")
    extra_approvers = fields.Many2many('hr.employee', 'hr_leave_employee_extra_approvers_rel', 'hr_leave_id', 'employee_id',
                            string="Extra Approvers", compute="_compute_extra_approvers", store=True, readonly=True)
    
    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].browse(employee_id)
        followers = employee.user_id.partner_id.ids + self.inform_to.user_id.partner_id.ids + self.extra_approvers.user_id.partner_id.ids
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
        
        past_limit_in_days_config = self.env['ir.config_parameter'].sudo().get_param('hr_holidays.past_limit_in_days')
        past_limit_in_days = int(past_limit_in_days_config) if past_limit_in_days_config else 0

        if not is_officer:
            crr_past_date_limit = fields.Date.today() - relativedelta(days=past_limit_in_days)
            if any(hol.date_from.date() < crr_past_date_limit and hol.employee_id.leave_manager_id != user for hol in self):
                limit_day_message = f'already begun over {past_limit_in_days} days ago' if past_limit_in_days > 0 else 'was in the past'
                raise UserError(_(f'You must have manager rights to modify/validate a time off that {limit_day_message}.'))
            
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
        
        if 'inform_to' in values:
            # Extract and store current inform_to ids before updating records
            current_inform_to = {leave.id: leave.inform_to.ids for leave in self}
            new_inform_to = values['inform_to'][0][2]
                
        # Model hr.leave inherit mail.thread
        # which mean: in hr.leave write method, super(HolidayRequest, self).write(values) call mail.thread's write method
        # So, in this case, where we completely override the whole write method
        # we need to call mail.thread's write method to keep the original behaviour
        result = super(type(self.env['mail.thread']), self).write(values)
        
        if employee_id and not context.get('leave_fast_create'):
            for holiday in self:
                holiday.add_follower(employee_id)
                
        if 'inform_to' in values and new_inform_to:
            self._send_mail_to_new_inform_to(current_inform_to, new_inform_to)
        
        return result
    
    def _send_mail_to_new_inform_to(self, current_inform_to, new_inform_to):
        new_inform_to_empl = self.env['hr.employee'].browse(new_inform_to)
        
        for leave in self:
            new_inform_to_send_mail_ids = set(new_inform_to) - set(current_inform_to.get(leave.id, []))
            new_inform_to_send_mail = new_inform_to_empl.filtered(lambda empl: empl.id in new_inform_to_send_mail_ids)
            leave.send_mail_to_inform_to(new_inform_to_send_mail, only_send_new=True)
        
    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env.user.employee_id
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')

        for holiday in self:
            val_type = holiday.validation_type

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee:
                        raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                        if not is_officer and self.env.user != holiday.employee_id.leave_manager_id and not self._is_an_extra_approvers():
                            raise UserError(_('You must be either %s\'s manager or Time off Manager to approve this leave') % (holiday.employee_id.name))
    
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
            
    @api.ondelete(at_uninstall=False)
    def _check_unlink_rights(self):
        crr_user = self.env.user
        is_timeoff_officer = crr_user.has_group('hr_holidays.group_hr_holidays_user')
        for leave in self:
            if  leave.state in ['draft', 'confirm'] and not (is_timeoff_officer or (leave.employee_id == crr_user.employee_id)):
                raise UserError('You are not allowed to delete this Time Off Request!')

    @api.depends('date_from', 'date_to')
    def _compute_extra_approvers(self):
        now = fields.Datetime.now()
        crr_user = self.env.user
        
        booked_resources = self.env['planning.calendar.resource'].search([
            ('employee_id', '=', crr_user.employee_id.id),
            '|', '|',
                '&',
                    ('start_date', '<=', self.request_date_from),
                    ('end_date', '>=', self.request_date_from),
                '&',
                    ('start_date', '<=', self.request_date_to),
                    ('end_date', '>=', self.request_date_to),
                '&',
                    ('start_date', '>=', self.request_date_from),
                    ('end_date', '<=', self.request_date_to),
        ])
        
        running_projects = booked_resources.project_id
        
        pm_ids = [
            project.user_id.employee_ids.id
            for project in running_projects
            if project.user_id.employee_ids
            and project.user_id != crr_user
            and project.user_id != crr_user.leave_manager_id
        ]
        
        for leave in self:
            leave.extra_approvers = [(6, 0, pm_ids)]

    def _is_an_extra_approvers(self):
        return self.env.user.employee_id in self.extra_approvers
    
    @api.depends_context('uid')
    def _compute_description(self):
        super(HrLeave, self)._compute_description()
        for leave in self:
            if leave._is_an_extra_approvers():
                leave.name = leave.sudo().private_name
            
    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrLeave, self).create(vals_list)
        records.send_mail_to_extra_approvers()
        records.send_mail_to_inform_to()
        return records
    
    def send_mail_by_template(self, template_id):
        template = self.env.ref(template_id, raise_if_not_found=False)
        template.send_mail(self.id, force_send=True)
        
    def send_mail_to_extra_approvers(self):
        self.send_mail_by_template('hr_holidays_updation.template_send_mail_extra_approvers')

    def send_mail_to_inform_to(self, new_inform=False, only_send_new=False):
        if only_send_new and not new_inform:
            return
        
        if new_inform:
            template = self.env.ref('hr_holidays_updation.template_send_mail_inform_to', raise_if_not_found=False)
            template.send_mail(self.id, force_send=True, email_values={'email_to': ','.join(emp.work_email for emp in new_inform) })
            return
        
        self.send_mail_by_template('hr_holidays_updation.template_send_mail_inform_to')
            
    def name_get(self):
        if self.env.context.get('short_name'):
            return super(HrLeave, self).with_context({'short_name': 0}).name_get()
        return super(HrLeave, self).name_get()