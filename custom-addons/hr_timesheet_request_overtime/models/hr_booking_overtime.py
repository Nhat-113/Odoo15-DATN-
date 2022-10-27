
from datetime import datetime
from odoo import api, fields, models, _
import pandas as pd
import json

from odoo.exceptions import ValidationError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    type_day_ot = fields.Selection([
        ('other', 'Other'),
        ('normal_day', 'Normal Day'),
        ('weekend', 'Weekend'),
        ('holiday', 'Holiday'),
    ], string='Type Day OT', index=True, copy=False, default='normal_day', tracking=True, required=True)

    request_overtime_ids = fields.Many2one('hr.request.overtime', string='Request Overtime', store=True, readonly=True)
    check_request_ot = fields.Boolean('Check Readonly', compute='_compute_request_overtime_id', store=True, default=False)
    check_approval_ot = fields.Boolean('Check Approvals', compute='_compute_request_overtime_id', store=True, default=False)

    @api.depends('request_overtime_ids.stage_id')
    def _compute_request_overtime_id(self):
        for record in self:
            if record.type_ot=='yes':
                if record.request_overtime_ids.stage_id.name == 'Submit':
                    record.write({'check_request_ot' : True})
                elif record.request_overtime_ids.stage_id.name == 'Approval':
                    record.write({'check_request_ot' : True})
                    record.write({'check_approval_ot' : True})
                else:
                    record.write({'check_request_ot' : False})
                    record.write({'check_approval_ot' : False})
            
            else:
                record.request_overtime_ids = False

    # Find reqeust overtime for timesheet when type_timesheet = 'type_ot'
    @api.model
    def create(self, vals_list):
        # TODO refactor this function
        type_timesheet = vals_list.get('type_ot')  
        if type_timesheet == 'yes':
            request_overtime = self.env['hr.request.overtime'].search([('project_id','=',vals_list['project_id']),
                                                                            ('start_date', '<=', vals_list['date']), ('end_date', '>=' , vals_list['date'])])
            if request_overtime.stage_id.name not in ['Submit', 'Approval']:
                user_booking_ids = [item.user_id.id for item in request_overtime.booking_overtime]

                if vals_list['employee_id'] in user_booking_ids:
                    booking_overtime = self.env['hr.booking.overtime'].search([('request_overtime_id','=', request_overtime.id), ('user_id','=', vals_list['employee_id'])])
                    
                    if booking_overtime.start_date <= datetime.strptime(vals_list['date'], '%Y-%m-%d').date() and booking_overtime.end_date >= datetime.strptime(vals_list['date'], '%Y-%m-%d').date():
                        values = {'request_overtime_ids': request_overtime.id}
                        vals_list.update(values)
                    else:
                        values = {'request_overtime_ids': False}
                        vals_list.update(values)
                else:
                    values = {'request_overtime_ids': False}
                    vals_list.update(values)
            else:
                values = {'request_overtime_ids': False}
                vals_list.update(values)
        else:
            values = {'request_overtime_ids': False}
            vals_list.update(values)

        return super().create(vals_list)

    @api.model
    def write(self, vals):
        result = super().write(vals)
        vals = self._check_change_value_timesheet()
        return super().write(vals)

    def _check_change_value_timesheet(self):
        # TODO refactor this function
        if self.type_ot == 'yes':

            request_overtime = self.env['hr.request.overtime'].search([('project_id','=',self.project_id.id),
                                                                            ('start_date', '<=', self.date), ('end_date', '>=' , self.date)])
                                    
            if request_overtime.stage_id.name not in ['Submit', 'Approval']:
                user_booking_ids = [item.user_id.id for item in request_overtime.booking_overtime]

                if self.employee_id.id in user_booking_ids:
                    booking_overtime = self.env['hr.booking.overtime'].search([('request_overtime_id','=', request_overtime.id), ('user_id','=', self.employee_id.id)])
                    
                    if booking_overtime.start_date <= self.date and booking_overtime.end_date >= self.date:
                        return {'request_overtime_ids': request_overtime.id}
                    else: 
                        return {'request_overtime_ids': False}
                else: 
                    return {'request_overtime_ids': False}
            else:
                return {'request_overtime_ids': False}
        else:
            return {'request_overtime_ids': False}
            
class HrBookingOvertime(models.Model):
    _name = "hr.booking.overtime"
    _inherit=['mail.thread']

    request_overtime_id = fields.Many2one('hr.request.overtime', string='Booking Overtime', readonly=False)
    
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

    booking_time_overtime = fields.Integer(string="Plan Overtime (Hours)",
                              readonly=False, help="The booking of working overtime in the project", default=False)

    actual_overtime = fields.Integer(string="Actual Overtime",
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

    @api.onchange("request_overtime_id.stage_id")
    def _compute_stage(self):
        for item in self:
            item.read_stage = item.request_overtime_id.stage_id.name


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
            "domain": 
                [('project_id', '=', self.request_overtime_id.project_id.id),
                ('employee_id', '=', self.user_id.id), ('type_ot','=','yes'),
                ('date', '>=' , self.start_date), ('date', '<=' ,self.end_date)]
        }
        return action

    @api.depends("request_overtime_id.stage_id")
    def _compute_actual_overtime(self):
        for item in self:
            list_timesheet_overtime = self.env['account.analytic.line'].search([('project_id', '=', item.request_overtime_id.project_id.id),\
                ('employee_id', '=', item.user_id.id), ('type_ot','=','yes')])
            
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
                'access_link': task._notify_get_action_link('view'),
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