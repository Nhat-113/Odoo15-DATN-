
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
                                ], string='Pay Type', index=True, default='full_day_off', tracking=True, required=True)

    type_day_ot = fields.Selection([
                                ('other', 'Other'),
                                ('normal_day', 'Normal Day'),
                                ('weekend', 'Weekend'),
                                ('holiday', 'Holiday'),
                                ], string='Type Day', index=True, copy=False, compute="compute_type_overtime_day", tracking=True, required=True, store=True)

    status_timesheet_overtime = fields.Selection([
                                        ('draft', 'To Confirm'),
                                        ('confirm', 'Confirm'),
                                        ('refuse', 'Refused'),
                                        ], default='draft', readonly=False, store=True, tracking=True, compute="reject_timesheet_overtime")
    reason_reject = fields.Char(string="Reason Refuse", help="Type Reason Reject Why Reject Task Score", readonly=False, tracking=True)
    
    def _readonly_resion_refuse(self):
        if self.env.user.has_group('hr_timesheet_request_overtime.request_overtime_access_user') == True:
            for task in self:
                task.read_only_reason_refuse = True
        else:
            for task in self:
                task.read_only_reason_refuse = False
                
    read_only_reason_refuse = fields.Boolean(compute=_readonly_resion_refuse, store=False)

    request_overtime_ids = fields.Many2one('hr.request.overtime', string='Request Overtime', store=True, readonly=True)
    check_request_ot = fields.Boolean('Check Readonly', compute='_compute_request_overtime_id', store=True, default=False)
    check_approval_ot = fields.Boolean('Check Approvals', compute='_compute_request_overtime_id', store=True, default=False)


    @api.onchange('date', 'type_ot', 'type_day_ot')
    def compute_type_overtime_day(self):
        for record in self:
            date = record.date
            public_holiday = self.env['resource.calendar.leaves'].search([('calendar_id','=',False),('holiday_id','=',False), 
            ('date_from','<=',date),('date_to','>=',date)])
            if record.type_day_ot != 'other':
                if public_holiday:
                    record.type_day_ot = 'holiday'
                elif  4 < date.weekday() < 7:
                    record.type_day_ot = 'weekend'
                else:
                    record.type_day_ot = 'normal_day'
            else:
                record.type_day_ot = 'other'

    @api.depends('reason_reject')
    def reject_timesheet_overtime(self):
        for timesheet in self:
            if timesheet.reason_reject != False:
                timesheet.status_timesheet_overtime = 'refuse'
            else:
                timesheet.status_timesheet_overtime = 'draft'

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
                    record.write({'check_request_ot': True})
                    record.write({'status_timesheet_overtime': 'confirm'})
                elif record.request_overtime_ids.stage_id.name == 'Approval':
                    record.write({'check_request_ot': True})
                    record.write({'check_approval_ot': True})
                    # Compute time off 'nghi bu' when change status Approvals
                    record._compute_pay_type_of_timeoff()
                    record.write({'status_timesheet_overtime': 'confirm'})
                else:
                    record.write({'check_request_ot': False})
                    record.write({'check_approval_ot': False})
                    record.write({'status_timesheet_overtime': 'draft'})
            
            else:
                record.request_overtime_ids = False


    def action_confirm_all_timesheet_overtime(self):
        for record in self:
            record.status_timesheet_overtime = 'confirm'

    # Find reqeust overtime for timesheet when type_timesheet = 'type_ot'
    @api.model
    def create(self, vals_list):
        # TODO refactor this function
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
                if booking and booking.request_overtime_id.stage_id.name not in ['Submit', 'Approval']:
                    values['request_overtime_ids'] =  booking.request_overtime_id.id
                else: 
                    values['request_overtime_ids'] = False
        else: 
            values['request_overtime_ids'] = False
            
        vals_list.update(values)
        return super().create(vals_list)

    def write(self, vals):
        values = self._check_change_value_timesheet(vals)
        vals.update(values)
        result = super(AccountAnalyticLine, self).write(vals)

        return result

    def _check_change_value_timesheet(self, vals):
        # TODO refactor this function
        if self.type_ot == 'yes':
            if 'date' in vals:
                date = vals['date']
            else:
                date =  self.date

            booking_overtime = self.env['hr.booking.overtime'].search(
                                            [('user_id','=', self.employee_id.id),
                                            ('start_date','<=', date), 
                                            ('end_date','>=', date)])

            if booking_overtime and booking_overtime.request_overtime_id.stage_id.name not in ['Submit', 'Approval'] or self.request_overtime_ids.id:
                return {'request_overtime_ids': booking_overtime.request_overtime_id.id}
            else: 
                return {'request_overtime_ids': False}
        else: 
            return {'request_overtime_ids': False}
            
class HrBookingOvertime(models.Model):
    _name = "hr.booking.overtime"
    _inherit=['mail.thread']

    request_overtime_id = fields.Many2one('hr.request.overtime', string='Booking Overtime', readonly=False)
    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True, compute='_compute_stage')
    
    user_id = fields.Many2one(
        'hr.employee', string='Member', required=True, help="Member name assgin overtime")

    user_id_domain = fields.Char(
        compute="_compute_user_id_domain",
        readonly=True,
        store=False,
    )

    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working overtime on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished overtime on project")

    duration = fields.Integer(compute='_compute_duration', string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=0)

    booking_time_overtime = fields.Float(string="Plan (Hours)",
                              readonly=False, help="The booking of working overtime in the project", required=True, default=0)

    actual_overtime = fields.Float(string="Actual Overtime",
                              readonly=False, help="The duration actual of working overtime in the project", compute="_compute_actual_overtime")
    
    inactive = fields.Boolean(string="Inactive Member", default=False, store=True)
    description = fields.Text("Description", translate=True)
    read_stage = fields.Char(string="Read Stage request overtime", compute="_compute_stage")

    @api.depends('start_date')
    def _compute_user_id_domain(self):
        for record in self:
            user_ids = record.request_overtime_id.project_id.planning_calendar_resources.employee_id.ids
            user_ids.append(self._uid)
            record.user_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    @api.constrains('start_date', 'end_date')
    def _validation_date_time(self):
        for record in self:
            if record.start_date < record.request_overtime_id.start_date or record.end_date > record.request_overtime_id.end_date:
                raise ValidationError(_("Booking Plan Date Overtime for Member must be within the duration of the Request Overtime."))

    @api.constrains('booking_time_overtime')
    def _check_value_plan_overtime(self):
        for record in self:
            if record.booking_time_overtime > 999 or record.booking_time_overtime <= 0:
                raise ValidationError(_('Please enter value plan Overtime between 1-999 (hour).'))
            
            # TODO Validation time OT khong vuot qua so gio tuong ung voi Duration
            # if record.duration:
            #     range_hour_plan = record.duration*8
            # if record.booking_time_overtime > range_hour_plan:
            #     raise ValidationError(_('Validation time OT khong vuot qua so gio tuong ung voi Duration'))

    @api.onchange("request_overtime_id.stage_id")
    def _compute_stage(self):
        for item in self:
            item.read_stage = item.request_overtime_id.stage_id.name
            item.project_id = item.request_overtime_id.project_id


    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for record in self:
            if record.inactive == False:
                if record.end_date and record.start_date:
                    working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                    record.end_date.strftime('%Y-%m-%d')))
                    record.duration = working_days if working_days > 0 else 1
                else:
                    record.duration = 1
            else:
                if record.start_date and record.inactive_date:
                    working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                    record.inactive_date.strftime('%Y-%m-%d')))
                    record.duration = working_days if working_days > 0 else 1
                else:
                    record.duration = 1

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