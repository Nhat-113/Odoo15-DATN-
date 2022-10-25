from odoo import api, fields, models, _

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

    @api.model
    def _get_default_stage_id(self):
        return self.env['hr.request.overtime.stage'].search([], limit=1).id

    name = fields.Char("Subject", required=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True)
    start_date = fields.Date(string="Start Date", required=False, tracking=True, store=True)
    end_date = fields.Date(string="End Date", required=False, tracking=True, store=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True, compute='_compute_project_manager')
    description = fields.Text(string="Description", tracking=True)
    stage_id = fields.Many2one('hr.request.overtime.stage', 'Stage', ondelete='restrict',
                            default=_get_default_stage_id, 
                            store=True, readonly=False,
                            group_expand='_read_group_stage_ids',
                            required=True, tracking=True,
                            # domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            )
    requester_id = fields.Many2one('res.users', string='Requester', required=True)
    request_creator_id = fields.Many2one('res.users', string='Request Creator', required=True)
    user_id = fields.Many2one('res.users', string='Project Manager', tracking=True, readonly=True, compute='_compute_project_manager')
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="All members has been assigned to the project", tracking=True)
    booking_overtime = fields.One2many('hr.booking.overtime', 'request_overtime_id', string='Booking Overtime')
    active = fields.Boolean(string='Invisible Refuse Button', default=True)
    refuse_reason_id = fields.One2many('hr.request.overtime.refuse.reason', 'request_overtime_ids', tracking=True)
    refuse_reason = fields.Char('Refuse Reason', tracking=True)
    
    submit_flag = fields.Boolean(default=False)
    confirm_flag = fields.Boolean(default=True)
    approve_flag = fields.Boolean(default=True)
    request_flag = fields.Boolean(default=True)

    stage_name = fields.Text(string="Name", compute = '_get_stage_name', default ="Draw")
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
        user_ids = [
            user.user_id.id for user in self.booking_overtime.employee_id]
        self.member_ids = self.env['res.users'].search([('id', 'in', user_ids)])

    @api.onchange('project_id')
    def _compute_project_manager(self):
        for item in self:
            item.user_id = item.project_id.user_id or False
            item.company_id = item.project_id.company_id or False

    def action_submit_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Submit')]).id
        self.submit_flag = False

        # Send mail submit (from pm to director)
        mail_template = "hr_timesheet_request_overtime.submit_request_overtime_template"
        subject_template = "Submit Request Overtime"

        self._send_message_auto_subscribe_notify_request_overtime({self: item.requester_id for item in self}, mail_template, subject_template)

    def action_confirm_request_overtime(self):
        self.stage_id = self.env['hr.request.overtime.stage'].search([('name', '=', 'Confirm')]).id
        self.confirm_flag=False

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

    @api.depends('stage_id')
    def _get_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name
            if record.stage_id.name =="Draw":
                self.confirm_flag = True
                self.submit_flag = True
                self.request_flag = True
                self.approve_flag = True
            if record.stage_id.name == "Submit":
                self.submit_flag =False
                self.confirm_flag = True
                self.request_flag = True
                self.approve_flag = True
            if record.stage_id.name == "Confirm":
                self.submit_flag =True
                self.confirm_flag = False
                self.request_flag = True
                self.approve_flag = True
            if record.stage_id.name == "Request":
                self.submit_flag =True
                self.confirm_flag = True
                self.request_flag = False
                self.approve_flag = True
            if record.stage_id.name == "Approval":
                self.submit_flag =True
                self.confirm_flag = True
                self.request_flag = True
                self.approve_flag = False

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
        if 'submit_flag' in vals_list:
            vals_list['submit_flag']=True

        return super().create(vals_list)
    