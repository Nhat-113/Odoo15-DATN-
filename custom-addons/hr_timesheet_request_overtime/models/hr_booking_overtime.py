
from odoo import api, fields, models, _
import pandas as pd
import json
from datetime import datetime, timedelta
from datetime import date

from odoo.exceptions import ValidationError, UserError

class HolidaysAllocation(models.Model):
    """ Allocation Requests Access specifications: similar to leave requests """
    _inherit = "hr.leave.allocation"
    _description = "Time Off Allocation"

    @api.ondelete(at_uninstall=False)
    def _unlink_if_correct_states(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        for holiday in self.filtered(lambda holiday: holiday.state not in ['draft', 'cancel', 'confirm']):
            if holiday.env.user.has_group('hr_timesheet.group_timesheet_manager') == False:
                raise UserError(_('You cannot delete an allocation request which is in %s state.') % (state_description_values.get(holiday.state),))

    
class AccountAnalyticLine(models.Model):
    _inherit = ["account.analytic.line"]

    pay_type = fields.Selection([
                                ('full_cash', 'Full Cash'),
                                ('half_cash_half_dayoff', 'Cash 5:5 Day Off'),
                                ('full_day_off', 'Full Date Off'),
                                ], string='Pay Type', index=True, default=False)

    type_day_ot = fields.Selection([
                                ('other', 'Other'),
                                ('normal_day', 'Normal Day'),
                                ('weekend', 'Weekend'),
                                ('holiday', 'Holiday'),
                                ], string='Type Day', index=True, copy=False, default=False)

    status_timesheet_overtime = fields.Selection([
                                        ('draft', 'To Confirm'),
                                        ('confirm', 'Confirm'),
                                        ('refuse', 'Refused'),
                                        ('approved', 'Approved'),
                                        ], default='draft', store=True, tracking=True, compute="reject_timesheet_overtime")
    reason_reject = fields.Char(string="Reason Refuse", help="Type Reason Reject Why Reject Task Score", readonly=False, tracking=True, default=False)
    invisible_button_confirm = fields.Boolean(default=False, help="Check invisible button Confirm")
    hr_leave_allocation_id = fields.Many2one('hr.leave.allocation', store=True, default=False)


    payment_month = fields.Selection([
                                ('1', 'Month 1'),
                                ('2', 'Month 2'),
                                ('3', 'Month 3'),
                                ('4', 'Month 4'),
                                ('5', 'Month 5'),
                                ('6', 'Month 6'),
                                ('7', 'Month 7'),
                                ('8', 'Month 8'),
                                ('9', 'Month 9'),
                                ('10', 'Month 10'),
                                ('11', 'Month 11'),
                                ('12', 'Month 12'),
                                    ],
                                    string="Payment Month", 
                                    help="Payment month when approved timesheet OT by Director", readonly=False, default=False)
    payment_flag = fields.Boolean(default=False, help="Check payment")

    def _get_years(self):
        year_list = []
        for i in range(date.today().year - 10, date.today().year + 10):
            year_list.append((str(i), str(i)))
        return year_list

    def _get_year_defaults(self):
        return str(date.today().year)
        
    get_year_tb = fields.Selection(selection=_get_years, default=_get_year_defaults, string='Payment Year', required=True, tracking=True)

    def _readonly_resion_refuse(self):
        if self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_user') == True and \
            self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_projmanager') == False:
            for record in self:
                record.read_only_reason_refuse = True
                record.invisible_button_confirm = True
        else:
            for record in self:
                record.read_only_reason_refuse = False
                record.invisible_button_confirm = False

    @api.depends('status_timesheet_overtime')
    def _compute_invisible_button_approved(self):
        for record in self:
            if record.status_timesheet_overtime == 'confirm' and self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_director') == True:
                record.invisible_button_approved = True
            else:
                record.invisible_button_approved = False
                
    invisible_button_approved = fields.Boolean(default=False, help="Check invisible button Approved", compute="_compute_invisible_button_approved", store=False)
    read_only_reason_refuse = fields.Boolean(compute=_readonly_resion_refuse, store=False)

    request_overtime_ids = fields.Many2one('hr.request.overtime', string='Request Overtime', store=True, readonly=True, default=False)
    check_request_ot = fields.Boolean('Check Readonly', store=True, default=False)
    check_approval_ot = fields.Boolean('Check Approvals', store=True, default=False)


    @api.onchange('date', 'type_ot', 'type_day_ot', 'pay_type')
    def compute_type_overtime_day(self):
        for record in self:
            date = datetime.combine(record.date, datetime.min.time()) - timedelta(hours = 7)
            public_holiday = record.env['resource.calendar.leaves'].search([('calendar_id','=',False),('holiday_id','=',False), 
            ('date_from','<=',date),('date_to','>=',date)])
            if record.type_day_ot != 'other':
                if public_holiday:
                    record.type_day_ot = 'holiday'
                elif  4 <= date.weekday() < 6:
                    record.type_day_ot = 'weekend'
                else:
                    record.type_day_ot = 'normal_day'
            else:
                record.type_day_ot = 'other'
            
    @api.onchange('type_ot')
    def _compute_pay_type(self):
        for record in self:
            if record.type_ot == "yes":
                if record.pay_type == False:
                    record.pay_type = 'full_day_off'
            else:
                record.pay_type = False

    @api.depends('reason_reject')
    def reject_timesheet_overtime(self):
        for timesheet in self:
            if timesheet.reason_reject != False:
                timesheet.status_timesheet_overtime = 'refuse'
            else:
                timesheet.status_timesheet_overtime = 'draft'

    # Send mail reject timesheet OT
    @api.onchange('reason_reject')
    def send_mail(self):
        for task in self:
            if task.reason_reject != '':
                self._task_message_auto_subscribe_notify_reject_timesheet({task: task.employee_id for task in task})
    
    @api.model
    def _task_message_auto_subscribe_notify_reject_timesheet(self, users_per_task):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env['ir.model.data']._xmlid_to_res_id('hr_timesheet_request_overtime.reject_timesheet', raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        task_model_description = 'Timesheets'
        for task, users in users_per_task.items():
            if not users:
                continue
            values = {
                'object': task,
                'model_description': task_model_description,
                'access_link': task.env['mail.thread']._notify_get_action_link('view'),
                'project_name': task.project_id.name,
                'task_name': task.task_id.display_name,
                'refuse_reason': task.reason_reject
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)
                task.env['mail.thread'].message_notify(
                    subject=_('You have been reject timesheet %s', task.name),
                    body=assignation_msg,
                    partner_ids=user.user_id.partner_id.ids,
                    record_name=task.display_name,
                    email_layout_xmlid='mail.mail_notification_light',
                    model_description=task_model_description,
                )


    def confirm_timesheet_overtime(self):
        for record in self:
            record.write({'status_timesheet_overtime': 'confirm'})
            record.check_request_ot = True

    def approved_timesheet_overtime(self):
        for record in self:
            record._compute_pay_type_of_timeoff()
            record.check_approval_ot = True
            record.write({  'status_timesheet_overtime': 'approved',
                            })
    def action_confirm_all_timesheet_overtime(self):
        for record in self:
            if record.status_timesheet_overtime != 'approved':
                record.status_timesheet_overtime = 'confirm'
                record.check_request_ot = True

    def action_approved_all_timesheet_overtime(self):
        for record in self:
            record._compute_pay_type_of_timeoff()
            record.check_approval_ot = True
            record.status_timesheet_overtime = 'approved'
            record.write({  'status_timesheet_overtime': 'approved',
                            })
            record.check_approval_ot = True

    def _compute_pay_type_of_timeoff(self):
        for record in self:
            if record.type_ot == 'yes' and\
                record.status_timesheet_overtime != 'approved' and\
                        record.pay_type in ['full_day_off', 'half_cash_half_dayoff']:
                
                pay_type = record.pay_type
                time_of_type = self.env['hr.leave.type'].search([('company_id','=',record.employee_id.company_id.id),('name', 'like', 'Nghỉ bù')])
                if len(time_of_type)==0:
                    raise ValidationError(_("Please Create Time Off Types: Nghỉ bù."))
                number_of_hours_display = 0
                               
                type_date = {'other':1, 'normal_day':1.5, 'weekend':2, 'holiday':3}

                if pay_type == 'full_day_off':
                    number_of_hours_display = record.unit_amount * type_date[record.type_day_ot]
                elif pay_type == 'half_cash_half_dayoff':
                    number_of_hours_display = record.unit_amount/2 * type_date[record.type_day_ot]

                number_of_days = number_of_hours_display/8
                
                vals = {
                    'holiday_type': 'employee',
                    'name': 'Nghỉ bù Overtime',
                    # Mac dinh lay nghi bu dau tien
                    'holiday_status_id': time_of_type[0].id,
                    'employee_id': record.employee_id.id,
                    'date_from': datetime.now(), 
                    'date_to': date(date.today().year, 12, 31),
                    'number_of_days': number_of_days, 
                    'number_of_hours_display': number_of_hours_display,
                    'notes': False,
                    'state': 'validate',
                    'duration_display': number_of_hours_display,
                    'multi_employee': False, 
                    # TODO fix number_of_hours_display
                }
                hr_leave_allocation_id = self.env['hr.leave.allocation'].create(vals)
                record.hr_leave_allocation_id = hr_leave_allocation_id.id
            else:
                continue

    # Find request overtime for timesheet when type_timesheet = 'type_ot'
    @api.model
    def create(self, vals_list):
        type_timesheet = vals_list.get('type_ot') 
        date = vals_list.get('date')
        employee = vals_list.get('employee_id')
        project_id = vals_list.get('project_id')
        values = {'payment_month': str(datetime.strptime(date, '%Y-%m-%d').month)}
        
        if type_timesheet == 'yes':
            # TODO check lai truong hop search ra nhieu hon 1 booking, CASE nay booking phai la duy nhat
            booking_overtime = self.env['hr.booking.overtime'].search(
                                            [('user_id','=', employee),
                                            ('start_date','<=', date), 
                                            ('end_date','>=', date),
                                            ('project_id','=', project_id)])
            for booking in booking_overtime:
                if booking and booking.request_overtime_id.stage_id.name not in ['Submit', 'Approved'] and booking.request_overtime_id.active==True:
                    values['request_overtime_ids'] =  booking.request_overtime_id.id
                elif booking.request_overtime_id.stage_id.name in ['Submit', 'Approved']: 
                    values['request_overtime_ids'] =  booking.request_overtime_id.id
                    values['payment_month'] = False
                    values['status_timesheet_overtime'] = 'draft'
                    values['payment_flag'] = True
        else: 
            values['request_overtime_ids'] = False
        
        # Update pay type of OT:
        if 'pay_type' not in values and type_timesheet == "no":
                vals_list.update({'pay_type': False})
        else: 
            vals_list.update({'pay_type': 'full_day_off'})

            
        vals_list.update(values)
        return super().create(vals_list)

    def write(self, vals):
        values = self._check_change_value_timesheet(vals)
        vals.update(values)
        return super(AccountAnalyticLine, self).write(vals)

    def _check_change_value_timesheet(self, vals):
        type_timesheet = vals.get('type_ot')  or self.type_ot
        date = vals.get('date') or self.date
        employee = vals.get('employee_id') or self.employee_id.id

        if type_timesheet == 'yes':
            booking_overtime = self.env['hr.booking.overtime'].search(
                                            [('user_id','=', employee),
                                            ('start_date','<=', date), 
                                            ('end_date','>=', date), 
                                            ('project_id','=', self.project_id.id),
                                            ])
            for booking in booking_overtime:
                if booking and booking.request_overtime_id.stage_id.name not in ['Submit', 'Approved'] or self.request_overtime_ids.id and booking.request_overtime_id.active==True:
                    return {'request_overtime_ids': booking.request_overtime_id.id}
                elif booking.request_overtime_id.stage_id.name in ['Submit', 'Approved']: 
                    return {'request_overtime_ids': booking.request_overtime_id.id,
                            'payment_month' : False,
                            'status_timesheet_overtime' : 'draft'}
        else: 
            return {'request_overtime_ids': False}

        return {'request_overtime_ids': False}

    def unlink(self):
        for record in self:
            if record.status_timesheet_overtime == 'approved' and record.env.user.has_group('hr_timesheet.group_timesheet_manager') == False:
                raise UserError(_("Can not delete Timesheet Approved!"))
            record.hr_leave_allocation_id.sudo().unlink()
        return super().unlink()
            
class HrBookingOvertime(models.Model):
    _name = "hr.booking.overtime"
    _inherit=['mail.thread']

    request_overtime_id = fields.Many2one('hr.request.overtime', string='Booking Overtime', readonly=False)
    project_id = fields.Many2one(related='request_overtime_id.project_id', string="Project", store=True)
    
    user_id = fields.Many2one(
        'hr.employee', string='Member', required=True, help="Member name assgin overtime")

    user_id_domain = fields.Char(
        compute="_compute_user_id_domain",
        readonly=True,
        store=False,
    )

    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working overtime on project",
                             default=fields.Date.today, store=True)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished overtime on project", store=True)

    duration = fields.Integer(string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=1, store=True, compute="_compute_duration")

    booking_time_overtime = fields.Float(string="Plan (Hours)",
                              readonly=False, help="The booking of working overtime in the project", required=True, default=0)

    actual_overtime = fields.Float(string="Actual Overtime",
                              readonly=False, help="The duration actual of working overtime in the project", compute="_compute_actual_overtime")
    
    inactive = fields.Boolean(string="Inactive Member", default=False, store=True)
    description = fields.Text("Description", translate=True)
    read_stage = fields.Char(string="Read Stage request overtime", compute="_compute_stage", store=True)

    @api.depends('project_id')
    def _compute_user_id_domain(self):
        for record in self:
            try:
                user_ids = record.request_overtime_id.project_id.planning_calendar_resources.employee_id.ids
            except:
                user_ids = []
            record.user_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

            
    @api.onchange("request_overtime_id.stage_id")
    def _compute_stage(self):
        self.read_stage = self.request_overtime_id.stage_id.name
        self.project_id = self.request_overtime_id.project_id.id


    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for record in self:
            if record.end_date and record.start_date:
                working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                record.end_date.strftime('%Y-%m-%d')))
                record.duration = working_days if working_days > 0 else 1
            else:
                record.duration = 1
            
    @api.constrains('booking_time_overtime','start_date', 'end_date')
    def _check_value_plan_overtime(self):
        for record in self:
            if record.end_date and record.start_date:
                if record.end_date < record.start_date:
                    raise ValidationError(_("The Start Date must be smaller than the End Date."))

                if record.booking_time_overtime > 999 or record.booking_time_overtime <= 0:
                    raise ValidationError(_('Please enter value Plan Hour between 1-999 (hour).'))

                # Validation Plan Hour (1 day = 24 hour)
                limit_hour = ((record.end_date - record.start_date).days + 1)*24
                if record.booking_time_overtime > limit_hour:
                    raise ValidationError(_("Plan Hour must be less {} (Hour).".format(limit_hour)))
            
                if (record.start_date < record.request_overtime_id.start_date or record.end_date > record.request_overtime_id.end_date):
                        raise ValidationError(_("Booking Plan Date Overtime for Member must be within the duration of the Request Overtime."))

                # Validation date time
                if not self.request_overtime_id.start_date or not self.request_overtime_id.end_date:
                        raise ValidationError(_("Please update plan (start date and end date) for Request Overtime."))

    def timesheets_overtime_detail_action(self):
        name_view = self.user_id.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "views": [[self.env.ref('hr_timesheet.hr_timesheet_line_tree').id, "tree"]],
            "context": {"create": False, "edit": True, "delete": False},
            "domain": 
                [('project_id', '=', self.request_overtime_id.project_id.id),
                ('employee_id', '=', self.user_id.id), ('type_ot','=','yes'),
                ('date', '>=' , self.start_date), ('date', '<=' ,self.end_date), ('request_overtime_ids.id', '!=' ,False)]
        }
        return action

    @api.depends("request_overtime_id.stage_id")
    def _compute_actual_overtime(self):
        for item in self:
            list_timesheet_overtime = self.env['account.analytic.line'].search([('project_id', '=', item.request_overtime_id.project_id.id),
                ('employee_id', '=', item.user_id.id), ('type_ot','=','yes'),
                ('date', '>=' , item.start_date), ('date', '<=' ,item.end_date), ('request_overtime_ids','=',item.request_overtime_id.id)])
            
            total_hour_spent_overtime = 0
            for record in list_timesheet_overtime:
                    total_hour_spent_overtime += record.unit_amount

            item.actual_overtime = total_hour_spent_overtime

    @api.model
    def create(self,vals):
        booking_overtime = super(HrBookingOvertime, self).create(vals)
        subject_template = 'You have been assigned to %s' % booking_overtime.request_overtime_id.display_name
        mail_template = "hr_timesheet_request_overtime.assign_request_overtime" 
        self._send_message_auto_subscribe_notify_assign_request_overtime({item: item.user_id for item in booking_overtime}, mail_template, subject_template)
        return booking_overtime
    
    @api.model
    def _send_message_auto_subscribe_notify_assign_request_overtime(self, users_per_task, mail_template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(mail_template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        for task, users in users_per_task.items():
            if not users:
                continue

            values = {
                'assign_name': task.user_id.name,
                'object': task.request_overtime_id,
                'model_description': "Plan Overtime",
                'access_link': task.request_overtime_id._notify_get_action_link_request('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.request_overtime_id.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = user.user_id.partner_id.ids,
                    record_name = task.request_overtime_id.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Plan Overtime",
                )