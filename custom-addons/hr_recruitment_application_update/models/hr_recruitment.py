from odoo import api, fields, models, SUPERUSER_ID, _
import json

from odoo.exceptions import UserError

class Applicant(models.Model):
    _inherit = 'hr.applicant'

    def _compute_domain_stage(self):
        if self.user_has_groups('hr_recruitment_application_update.group_hr_recruitment_director')==False:
            return json.dumps([('name', 'in', ['Initial Qualification', 'Confirm CV', 'Interview'])])
        else:
            return json.dumps([('name', 'in', ['Initial Qualification', 'Confirm CV', 'Interview', 'Contract Proposal', 'Contract Signed'])])
   
    application_date = fields.Date(string='Application Date')
    recruitment_requester = fields.Many2many('hr.employee', string="Requester", help="Employees who make a recruitment request.", copy=False, required=True)
    stage_id = fields.Many2one('hr.recruitment.stage', 'Stage', ondelete='restrict', tracking=True,
                            compute='_compute_stage', store=True, readonly=False,
                            domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            group_expand='_read_group_stage_ids')                     
    stage_name = fields.Char(compute ="_compute_stage_name")
    check_send_mail_confirm = fields.Boolean("Check send mail confirm CV", default=False)
    check_pass_interview = fields.Boolean("Check pass interview", default=False)
    evaluation_applicant = fields.Html("Evaluation applicant")
    salary_percentage = fields.Float(string="Percentage Salary")
    work_month = fields.Integer(string="Work Month")
    user_send_mail = fields.Char(string="Get user send mail")
    step_confirm = fields.Integer(string="Count step confirm CV", default=0)
    last_stage = fields.Integer(string="ID last stage", default=0)

    salary_proposed = fields.Monetary("Proposed Salary", group_operator="avg", help="Salary Proposed by the Organisation")
    salary_expected = fields.Monetary("Expected Salary", group_operator="avg", help="Salary Expected by Applicant")
    salary_proposed_float = fields.Float("Proposed Salary", group_operator="avg", help="Salary Proposed by the Organisation", compute="_compute_salary")
    currency_id = fields.Many2one('res.currency', string="Currency",
                                 related='company_id.currency_id',
                                 default=lambda
                                 self: self.env.user.company_id.currency_id.id)

    check_contract_click = fields.Boolean("Check contract click", default=False)
    check_signed_click = fields.Boolean("Check signed click", default=False)
    stage_field_name = fields.Char("Stage name")
    date_closed = fields.Datetime("Hire Date", compute='_compute_date_closed', store=True, index=True, readonly=False, tracking=True)
    user_click_name = fields.Char('User click name', default=False)

    def _get_hide_plus_sign(self):
        for item in self:
            if self.user_has_groups('hr_recruitment_application_update.group_hr_recruitment_director')==False:
                item.check_hide_sign_plus = False
            else:
                item.check_hide_sign_plus = True

    check_hide_sign_plus = fields.Boolean("Check hide sign plus in salary field with pm role", compute="_get_hide_plus_sign")

    @api.depends('salary_proposed','salary_expected')
    def _compute_salary(self):
        for item in self:
            item.salary_proposed_float = float(item.salary_proposed)
        return

    @api.depends('job_id')
    def _compute_stage(self):
        for applicant in self:
            if applicant.job_id:
                if not applicant.stage_id:
                    stage_ids = self.env['hr.recruitment.stage'].search([
                        '|',
                        ('job_ids', '=', False),
                        ('job_ids', '=', applicant.job_id.id),
                        ('fold', '=', False)
                    ], order='sequence asc', limit=1).ids
                    applicant.stage_id = stage_ids[0] if stage_ids else False
            else:
                applicant.stage_id = self.env['hr.recruitment.stage'].search([('name','=','Initial Qualification')])

    @api.constrains('stage_id')
    def check_role_stage_kanban(self):
        if self.user_has_groups('hr_recruitment_application_update.group_hr_recruitment_project_manager') \
        and self.stage_id.name in ["Contract Proposal", "Contract Signed"] \
        and self.user_has_groups('hr_recruitment_application_update.group_hr_recruitment_director')==False:
            raise UserError("This action is out of authorization")

    @api.depends('stage_id.hired_stage')
    def _compute_date_closed(self):
        for applicant in self:
            applicant.check_contract_click = False
            if applicant.stage_id and applicant.stage_id.hired_stage and not applicant.date_closed:
                applicant.date_closed = fields.datetime.now()
            if not applicant.stage_id.hired_stage:
                applicant.date_closed = False

    @api.model
    def create(self, vals):
        result = super(Applicant, self).create(vals)
        result._send_mail_create_application()
        return result

    def _send_mail_create_application(self):
        template = 'hr_recruitment_application_update.new_application_message'
        subject_template = "Create Application"
        self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in self}, template, subject_template)
        self.last_stage = self.stage_id.id

    def _send_mail_hearing_cv(self):
        template = 'hr_recruitment_application_update.hearing_cv_application_message'
        subject_template = "Hearing CV"
        self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in self}, template, subject_template)
    
    def confirm_cv(self):
        self.check_pass_interview = False
        self.check_contract_click = False
        self.check_signed_click = False

        template = 'hr_recruitment_application_update.confirm_cv_message'
        subject_template = "Confirm CV"

        for record in self:
            self._send_message_auto_subscribe_notify_recruitment({item: item.user_id.employee_id for item in self}, template, subject_template)
            record.check_send_mail_confirm = True
        return record

    @api.depends('stage_id')
    def _compute_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name

            # Send mail hearing CV
            if record.stage_id.name == "Confirm CV" and \
                record.last_stage == self.env['hr.recruitment.stage'].search([('name','=','Initial Qualification')]).id:

                if record.id:
                    self._send_mail_hearing_cv()
                    record.last_stage = self.stage_id.id

                    self.check_pass_interview = False
                    self.check_contract_click = False
                    self.check_signed_click = False
                    self.check_send_mail_confirm = False
                else:
                    self.check_pass_interview = False

            # Send mail Sign
            if record.stage_id.name == 'Contract Signed' and not self.check_signed_click and record.id:
                self.send_mail_signed()
                self.check_signed_click = True
                record.last_stage = self.stage_id.id

                self.check_pass_interview = False
                self.check_contract_click = False
                self.check_send_mail_confirm = False    

            if record.stage_id.name == 'Contract Proposal':
                self.check_signed_click = False
                self.check_pass_interview = False
                self.check_send_mail_confirm = False    

            # Reset flag with stage is Initial Qualification
            if record.stage_id.name == 'Initial Qualification':
                self.check_signed_click = False
                self.check_pass_interview = False
                self.check_send_mail_confirm = False  
                self.check_contract_click = False
        

    def applicant_pass_interview(self):
        for item in self:
            item.check_pass_interview = True
            item.check_send_mail_confirm = False
            item.check_contract_click = False

            template = 'hr_recruitment_application_update.pass_interview_message'
            subject_template = "Pass Interview"
            self._send_message_auto_subscribe_notify_recruitment({item: item.user_id.employee_id for item in self}, template, subject_template)
    
    def confirm_contract_click(self):
        self.check_contract_click = True
        self.check_pass_interview = False

        template = 'hr_recruitment_application_update.confirm_contract'
        subject_template = "Confirm Contract"
        for item in self:
            self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in item}, template, subject_template)

    def send_mail_signed(self):
        self.check_pass_interview = False

        template = 'hr_recruitment_application_update.contract_sign_application_message'
        subject_template = "Contract Signed"

        for item in self:
            self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in item}, template, subject_template)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        job_id = self._context.get('default_job_id')
        search_domain = [('job_ids', '=', False)]
        if job_id:
            search_domain = ['|', ('job_ids', '=', job_id)] + search_domain
        if stages:
            search_domain = ['|', ('id', 'in', stages.ids)] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    @api.model
    def _send_message_auto_subscribe_notify_recruitment(self, users_per_task, template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        task_model_description = self.env['ir.model']._get(self._name).display_name
        for task, users in users_per_task.items():
            if not users:
                continue
            values = {
                'object': task,
                'model_description': task_model_description,
                'access_link': task._notify_get_action_link('view'),
            }
            
            for user in users:
                if self.pool.get('res.users').has_group(user.user_id, 'hr_recruitment_application_update.group_hr_recruitment_project_manager') \
                and self.stage_id.name in ["Contract Proposal", "Contract Signed"] \
                and self.pool.get('res.users').has_group(user.user_id,'hr_recruitment_application_update.group_hr_recruitment_director')==False:
                    continue
                
                self.user_send_mail = user.name
                self.user_click_name = self.env.user.display_name
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.message_notify(
                    subject = _('%s : %s', subject_template, task.job_id.name),
                    body = assignation_msg,
                    partner_ids = self.env['res.users'].search([('employee_ids.id','=',user.id)]).partner_id.ids,
                    record_name = task.display_name,
                    email_layout_xmlid = 'mail.mail_notification_light',
                    model_description = task_model_description,
                )

    def sent_mail_offer(self):
            """
            This function opens a window to compose an email, with the edit payslip template message loaded by default
            """
            self.ensure_one()
            try:
                template = self.env.ref('hr_recruitment_application_update.email_offer_for_candidate_template', False)
            except ValueError:
                template = False

            if self.id != self.env.user.employee_id.id:
                values = {'name':self.partner_name, 'email':self.email_from}
                result = self.env['res.partner'].create(values)
                try:
                    compose_form_id = self.env.ref(
                        'mail.email_compose_message_wizard_form').id
                except ValueError:
                    compose_form_id = False
                ctx = dict(
                    default_model='hr.applicant',
                    default_res_id=self.id,
                    default_use_template=bool(template),
                    default_template_id=template and template.id or False,
                    default_composition_mode='comment',
                )
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id, 'form')],
                    'view_id': compose_form_id,
                    'target': 'new',
                    'context': ctx,
                }