
from odoo import api, fields, models, _
import pandas as pd
import json
from datetime import datetime
from datetime import date

from odoo.exceptions import ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = ["account.analytic.line"]

    pay_type = fields.Selection([
                                ('full_cash', 'Full Cash'),
                                ('half_cash_half_dayoff', 'Cash 5:5 Date Off'),
                                ('full_day_off', 'Full Date Off'),
                                ], string='Pay Type', index=True, tracking=True, default=False)

    type_day_ot = fields.Selection([
                                ('other', 'Other'),
                                ('normal_day', 'Normal Day'),
                                ('weekend', 'Weekend'),
                                ('holiday', 'Holiday'),
                                ], string='Type Day', index=True, copy=False, compute="compute_type_overtime_day", tracking=True, required=True, store=True, default=False)

    status_timesheet_overtime = fields.Selection([
                                        ('draft', 'To Confirm'),
                                        ('confirm', 'Confirm'),
                                        ('refuse', 'Refused'),
                                        ], default='draft', readonly=False, store=True, tracking=True, compute="reject_timesheet_overtime")
    reason_reject = fields.Char(string="Reason Refuse", help="Type Reason Reject Why Reject Task Score", readonly=False, tracking=True, default=False)
    invisible_button_confirm = fields.Boolean(default=False, help="Check invisible button Confirm")
    
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
                
    read_only_reason_refuse = fields.Boolean(compute=_readonly_resion_refuse, store=False)

    request_overtime_ids = fields.Many2one('hr.request.overtime', string='Request Overtime', store=True, readonly=True, default=False)
    check_request_ot = fields.Boolean('Check Readonly', compute='_compute_request_overtime_id', store=True, default=False)
    check_approval_ot = fields.Boolean('Check Approvals', compute='_compute_request_overtime_id', store=True, default=False)


    @api.onchange('date', 'type_ot', 'type_day_ot')
    def compute_type_overtime_day(self):
        date = self.date
        public_holiday = self.env['resource.calendar.leaves'].search([('calendar_id','=',False),('holiday_id','=',False), 
        ('date_from','<=',date),('date_to','>=',date)])
        if self.type_day_ot != 'other':
            if public_holiday:
                self.type_day_ot = 'holiday'
            elif  4 < date.weekday() < 7:
                self.type_day_ot = 'weekend'
            else:
                self.type_day_ot = 'normal_day'
        else:
            self.type_day_ot = 'other'
        
        if self.type_ot == "no":
            self.pay_type = False
        elif self.pay_type == False:
            self.pay_type = "full_day_off"


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

    def approve_timesheet_overtime(self):
        for record in self:
            record.write({'status_timesheet_overtime': 'confirm'})

    def _compute_pay_type_of_timeoff(self):
        for record in self:
            if record.request_overtime_ids and record.type_ot == 'yes' and record.request_overtime_ids.stage_id.name=='Approval':
                pay_type = record.pay_type
                time_of_type = self.env['hr.leave.type'].search([('company_id','=',record.employee_id.company_id.id),('name', 'like', 'Nghỉ bù')])
                number_of_hours_display = 0
                if pay_type=='full_day_off':
                    number_of_hours_display = record.unit_amount
                elif pay_type=='half_cash_half_dayoff':
                    number_of_hours_display = record.unit_amount/2

                number_of_days = number_of_hours_display/8
                
                vals = {
                    'holiday_type': 'employee',
                    'name': 'Nghỉ bù Overtime',
                    'holiday_status_id': time_of_type.id,
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
                self.env['hr.leave.allocation'].create(vals)
            else:
                continue

    @api.depends('request_overtime_ids.stage_id')
    def _compute_request_overtime_id(self):
        for record in self:
            if record.type_ot=='yes':
                if record.request_overtime_ids.stage_id.name == 'Submit':
                    record.check_request_ot = True
                    record.status_timesheet_overtime = 'confirm'
                elif record.request_overtime_ids.stage_id.name == 'Approval':
                    record.check_request_ot = True
                    record.check_approval_ot = True
                    # Compute time off 'nghi bu' when change status Approvals
                    record._compute_pay_type_of_timeoff()
                    record.status_timesheet_overtime = 'confirm'
                else:
                    record.check_request_ot = False
                    record.check_approval_ot = False
                    
                    # Reset status timesheets OT when refuse
                    if record.request_overtime_ids.active == False:
                        record.status_timesheet_overtime = 'draft'

            else:
                record.request_overtime_ids = False


    def action_confirm_all_timesheet_overtime(self):
        for record in self:
            record.status_timesheet_overtime = 'confirm'

    # Find reqeust overtime for timesheet when type_timesheet = 'type_ot'
    @api.model
    def create(self, vals_list):
        type_timesheet = vals_list.get('type_ot') 
        date = vals_list.get('date')
        employee = vals_list.get('employee_id')
        project_id = vals_list.get('project_id')
        values = {}
        
        if type_timesheet == 'yes':
            # TODO check lai truong hop search ra nhieu hon 1 booking, CASE nay booking phai la duy nhat
            booking_overtime = self.env['hr.booking.overtime'].search(
                                            [('user_id','=', employee),
                                            ('start_date','<=', date), 
                                            ('end_date','>=', date),
                                            ('project_id','=', project_id)])
            for booking in booking_overtime:
                if booking and booking.request_overtime_id.stage_id.name not in ['Submit', 'Approval'] and booking.request_overtime_id.active==True:
                    values['request_overtime_ids'] =  booking.request_overtime_id.id
                else: 
                    values['request_overtime_ids'] = False
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
        result = super(AccountAnalyticLine, self).write(vals)

        return result

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
                if booking and booking.request_overtime_id.stage_id.name not in ['Submit', 'Approval'] or self.request_overtime_ids.id and booking.request_overtime_id.active==True:
                    return {'request_overtime_ids': booking.request_overtime_id.id}
                else: 
                    return {'request_overtime_ids': False}
        else: 
            return {'request_overtime_ids': False}

        return {'request_overtime_ids': False}
            
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

    @api.depends('start_date')
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
            
    @api.constrains('booking_time_overtime')
    def _check_value_plan_overtime(self):
        for record in self:
            if record.end_date and record.start_date:
                if record.end_date < record.start_date:
                    raise ValidationError(_("Start Date must be smaller than End Date"))

                if record.booking_time_overtime > 999 or record.booking_time_overtime <= 0:
                    raise ValidationError(_('Please enter value Plan Hour between 1-999 (hour).'))

                # Validation Plan Hour (1 day = 24 hour)
                limit_hour = ((record.end_date - record.start_date).days + 1)*24
                if record.booking_time_overtime > limit_hour:
                    raise ValidationError(_("Plan Hour must be less {} (Hour).".format(limit_hour)))

    @api.onchange('start_date', 'end_date')
    def _validation_duration(self):
        # Raise with datetime not in plan
        if self.end_date and self.start_date:
            # Validation date time
            if self.start_date > self.end_date:
                raise ValidationError(_("Start Date must be smaller than End Date."))

            if not self.request_overtime_id.start_date or not self.request_overtime_id.end_date:
                    raise ValidationError(_("Please update plan (start date and end date) for Request Overtime."))
                
            if (self.start_date < self.request_overtime_id.start_date or self.end_date > self.request_overtime_id.end_date):
                    raise ValidationError(_("Booking Plan Date Overtime for Member must be within the duration of the Request Overtime."))

            # Validation assigned member duplicate plan
            member_booking = self.request_overtime_id.booking_overtime[:-1]
            if member_booking:
                for booking in member_booking:
                    # Validation
                    if (self.user_id.id==booking.user_id.id) and \
                        ((self.start_date <= booking.start_date and self.end_date >= booking.start_date) or\
                            (self.start_date <= booking.end_date and self.end_date >= booking.end_date) or\
                                (self.start_date >= booking.start_date and self.end_date <= booking.end_date)):
                        raise ValidationError(_("The user is booked OT on this date, please recheck."))


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