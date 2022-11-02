from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import pandas as pd


class HrRequestOvertimeStage(models.Model):
    _name = "hr.request.overtime.stage"
    _description = "Timesheet Request Overtime Stages"
    _order = 'sequence'

    name = fields.Char("Stage Name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")
    confirm_stage = fields.Boolean('Confirm Stage',
        help="...")
    
    @api.model
    def create(self, vals_list):
        return super().create(vals_list)
    

class HrRequestOverTime(models.Model):
    _name = "hr.request.overtime"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = "Hr Request Overtime"
    _order = "id DESC"

    def _get_default_stage_id(self):
        return self.env['hr.request.overtime.stage'].search([], limit=1).id

    def _get_default_approve(self):
        return self.env.user.employee_id.parent_id.user_id.ids

    name = fields.Char("Subject", required=True)

    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True)
    start_date_project = fields.Date(string="Start Date", required=False,store=True, compute='_compute_project_info')
    end_date_project = fields.Date(string="End Date", required=False, store=True, compute='_compute_project_info')
    
    start_date = fields.Date(string="Start Date", required=True, tracking=True, store=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True, store=True)
    duration_overtime = fields.Integer(compute='_compute_duration_overtime', string="Duration (Working day)",
                              readonly=True, help="The duration of working overtime in the project", default=0)

    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True, compute='_compute_project_info')
    description = fields.Text(string="Description", tracking=True)
    stage_id = fields.Many2one('hr.request.overtime.stage', 'Stage', ondelete='restrict',
                            default=_get_default_stage_id, 
                            store=True, readonly=False,
                            group_expand='_read_group_stage_ids',
                            required=True, tracking=True,
                            # domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            )
    request_creator_id = fields.Many2one('res.users', string='Inform to', required=True, default=lambda self: self.env.user)
    requester_id = fields.Many2many('res.users', string='Approvals', required=True, default=lambda self: self._get_default_approve(), readonly=False)
    user_id = fields.Many2one('res.users', string='Project Manager', tracking=True, readonly=True, compute='_compute_project_info')
    member_ids = fields.Many2many('hr.employee', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    booking_overtime = fields.One2many('hr.booking.overtime', 'request_overtime_id', string='Booking Overtime')
    active = fields.Boolean(string='Invisible Refuse Button', default=True)
    refuse_reason_id = fields.One2many('hr.request.overtime.refuse.reason', 'request_overtime_ids', tracking=True)
    refuse_reason = fields.Char('Refuse Reason', tracking=True)
    
    submit_flag = fields.Boolean(default=True)
    confirm_flag = fields.Boolean(default=True)
    approve_flag = fields.Boolean(default=True)
    request_flag = fields.Boolean(default=False)

    stage_name = fields.Text(string="Name", compute = '_get_stage_name', default ="Draft", store=True)
    last_stage = fields.Integer(string="Last stage", default=0)
    
    def action_refuse_reason(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Reason'),
            'res_model': 'hr.request.overtime.refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_overtime_ids': self.id},
            'views': [[False, 'form']]
        }
       
    def reset_request_overtime(self):
        """ Reinsert the request into the recruitment pipe in the first stage"""
        default_stage = self.env['hr.request.overtime.stage'].search([], order='sequence asc', limit=1).id
        for request in self:
            request.write(
                {'stage_id': default_stage})

    def toggle_active(self):
        res = super(HrRequestOverTime, self).toggle_active()
        request_active = self.filtered(lambda request: request.active)
        if request_active:
            request_active.reset_request_overtime()
        
        request_overtime_inactive = self.filtered(lambda request: not request.active)
        if request_overtime_inactive:
            return request_overtime_inactive.action_refuse_reason()
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Always display all stages """
        return stages.search([], order=order)

    @api.onchange('booking_overtime')
    def _add_booking_overtime(self):
        # update member_ids list
        for record in self:
            user_ids = [
                user.id for user in record.booking_overtime.user_id]
            record.member_ids = self.member_ids = self.env['hr.employee'].search(
            [('id', 'in', user_ids)])

    @api.onchange('project_id')
    def _compute_project_info(self):
        for item in self:
            item.user_id = item.project_id.user_id or False
            item.company_id = item.project_id.company_id or False
            item.start_date_project = item.project_id.date_start
            item.end_date_project = item.project_id.date

    @api.depends('start_date', 'end_date')
    def _compute_duration_overtime(self):
        """ Calculates duration working time"""
        for record in self:
            if record.end_date and record.start_date:
                working_days = len(pd.bdate_range(record.start_date.strftime('%Y-%m-%d'),
                                                record.end_date.strftime('%Y-%m-%d')))
                record.duration_overtime = working_days if working_days > 0 else 1
            else:
                record.duration_overtime = 1

    @api.constrains('start_date', 'end_date')
    def _validate_plan_overtime(self):
        for record in self:
            # Validation Plan Date Overtime must be within the duration of the project
            if (record.project_id.date_start and record.project_id.date) and \
                (record.start_date < record.project_id.date_start or record.end_date > record.project_id.date):
                    raise ValidationError(_("Plan Date Overtime must be within the duration of the project."))

            # Validation Plan Date Overtime not overlap in the same project
            project_request_overtime = self.env['hr.request.overtime'].search([('project_id', '=' ,record.project_id.id),('id','!=' ,record.id)])
            for item in project_request_overtime:
                if item.end_date < record.start_date or item.start_date > record.end_date:
                    return
                else:
                    raise ValidationError(_("Plan Date Overtime can not overlap in the same project. \nRequest Overtime Duplicate Plan is: {}".format(item.name)))

    def action_submit_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Submit')]).id
        self.submit_flag = False

        # Send mail submit (from pm to director)
        mail_template = "hr_timesheet_request_overtime.submit_request_overtime_template"
        subject_template = "Submit Request Overtime"

        self._send_message_auto_subscribe_notify_request_overtime({self: item.requester_id for item in self}, mail_template, subject_template)

    def action_confirm_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Confirm')]).id
        self.confirm_flag = False

        # Send mail confirm (from director to pm)
        mail_template = "hr_timesheet_request_overtime.confirm_request_overtime_template"
        subject_template = "Confirm Request Overtime"
        self._send_message_auto_subscribe_notify_request_overtime({self: item.request_creator_id for item in self}, mail_template, subject_template)

    def action_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Request')]).id
        self.approve_flag = False

        # Send mail request timesheets ot (from pm to director)
        mail_template = "hr_timesheet_request_overtime.request_timesheets_overtime_template"
        subject_template = "Request Timesheets Overtime"
        self._send_message_auto_subscribe_notify_request_overtime({self: item.requester_id for item in self}, mail_template, subject_template)

    def action_approve_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Approval')]).id
        self.approve_flag = False

        # Send mail approvals request overtime (from director to pm)
        mail_template = "hr_timesheet_request_overtime.approvals_request_overtime_template"
        subject_template = "Approvals Request Timesheets Overtime"
        self._send_message_auto_subscribe_notify_request_overtime({self: item.request_creator_id for item in self}, mail_template, subject_template)

    # TODO Fix this, refator code
    @api.depends('stage_id')
    def _get_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name
            if record.stage_id.name =="Draft":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Request":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': False,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Confirm":
                vals = {
                'confirm_flag': False,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Submit":
                vals = {
                'confirm_flag': True,
                'submit_flag': False,
                'request_flag': True,
                'approve_flag': True,
                }
                self.write(vals)
            if record.stage_id.name == "Approval":
                vals = {
                'confirm_flag': True,
                'submit_flag': True,
                'request_flag': True,
                'approve_flag': False,
                }
                self.write(vals)

    @api.model
    def _send_message_auto_subscribe_notify_request_overtime(self, users_per_task, mail_template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(mail_template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        for task, users in users_per_task.items():
            if not users:
                continue
            values = {
                'object': task,
                'model_description': "Request",
                'access_link': task._notify_get_action_link('view'),
            }
            
            for user in users:
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.message_notify(
                    subject = subject_template,
                    body = assignation_msg,
                    partner_ids = user.partner_id.ids,
                    record_name = task.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = "Request Overtime",
                )
    
    @api.model
    def create(self, vals_list):
        if 'request_flag' in vals_list:
            vals_list['request_flag']=True

        return super().create(vals_list)
    