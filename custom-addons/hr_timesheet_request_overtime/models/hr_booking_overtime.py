
from odoo import api, fields, models
import pandas as pd


class HrBookingOvertime(models.Model):
    _name = "hr.booking.overtime"
    _inherit=['mail.thread']

    request_overtime_id = fields.Many2one('hr.request.overtime', string='Booking Overtime', readonly=False)
    
    employee_id = fields.Many2one(
        'hr.employee', string='Member', required=True, help="Member name assgin overtime")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working overtime on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished overtime on project")

    duration = fields.Integer(compute='_compute_duration', string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=1)

    booking_time_overtime = fields.Integer(string="Plan Overtime",
                              readonly=False, help="The booking of working overtime in the project", default=False)

    actual_overtime = fields.Integer(string="Actual Overtime",
                              readonly=False, help="The duration actual of working overtime in the project", compute="_compute_actual_overtime")
    
    inactive = fields.Boolean(string="Inactive Member", default=False, store=True)
    description = fields.Text("Description", translate=True)
    read_stage = fields.Char(string="Read Stage request overtime", compute="_compute_stage")

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
        name_view = self.employee_id.name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            "res_model": "account.analytic.line",
            "views": [[self.env.ref('hr_timesheet.hr_timesheet_line_tree').id, "tree"]],
            "domain": 
                [('project_id', '=', self.request_overtime_id.project_id.id),
                ('employee_id', '=', self.employee_id.id), ('type_ot','=','yes')]
        }
        return action

    @api.depends("request_overtime_id.stage_id")
    def _compute_actual_overtime(self):
        for item in self:
            list_timesheet_overtime = self.env['account.analytic.line'].search([('project_id', '=', item.request_overtime_id.project_id.id),\
                ('employee_id', '=', item.employee_id.id), ('type_ot','=','yes')])
            
            total_hour_spent_overtime = 0
            for record in list_timesheet_overtime:
                    total_hour_spent_overtime += record.unit_amount

            item.actual_overtime = total_hour_spent_overtime

    @api.model
    def create(self,vals):
        booking_overtime = super(HrBookingOvertime, self).create(vals)
        subject_template = 'You have been assigned to %s' % booking_overtime.request_overtime_id.display_name
        mail_template = "hr_timesheet_request_overtime.assign_request_overtime" 
        self._send_message_auto_subscribe_notify_assign_request_overtime({item: item.employee_id for item in booking_overtime}, mail_template, subject_template)
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

            #TODO Fix get access link -> remote access_link when deploy product
            access_link = task.request_overtime_id._notify_get_action_link('view').replace('https://taskmanagement.d-soft.tech','http://192.168.4.58:8089')

            values = {
                'assign_name': task.employee_id.name,
                'object': task.request_overtime_id,
                'model_description': "Plan Overtime",
                'access_link': access_link,
                # 'access_link': task._notify_get_action_link('view'),
            }
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.request_overtime_id.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = self.env['res.users'].search([('employee_ids.id','=',user.id)]).partner_id.ids,
                    record_name = task.request_overtime_id.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Plan Overtime",
                )