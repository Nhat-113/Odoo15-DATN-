from odoo import api, fields, models, SUPERUSER_ID, _
import json

from odoo.exceptions import UserError

class Applicant(models.Model):
    _inherit = 'hr.applicant'

    def _compute_domain_stage(self):
        if self.user_has_groups('hr_recruitment.group_hr_recruitment_user')==False:
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

    @api.model
    def create(self, vals):
        result = super(Applicant, self).create(vals)
        result.send_mail_confirm_cv()
        return result

    @api.depends('stage_id')
    def _compute_stage_name(self):
        for record in self:
            record.stage_name = record.stage_id.name
            try:
                if record.stage_name == "Interview" and record.check_send_mail_confirm==False:
                    self.send_mail_confirm_cv()
                    record.check_send_mail_confirm=True
                elif record.stage_name == "Confirm CV":
                    self.send_mail_confirm_cv()
            except:
                continue

    @api.onchange('stage_id')
    def check_role_stage_kanban(self):
        if self.user_has_groups('hr_recruitment_application_update.group_hr_recruitment_project_manager') and self.stage_id.name=="Interview":
            raise UserError("This action is out of authorization")
        
    def confirm_cv(self):
        for record in self:
            stage = self.env["hr.recruitment.stage"].search([("name",'=' ,'Interview')])
            record.stage_id = stage
            self.send_mail_confirm_cv()
            record.check_send_mail_confirm=True
        return record

    def applicant_pass_interview(self):
        for item in self:
            item.check_pass_interview = True
            self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in item})

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

    def send_mail_confirm_cv(self):
        for item in self:
            self._send_message_auto_subscribe_notify_recruitment({item: item.recruitment_requester for item in item})

    # send mail confirm CV
    @api.model
    def _send_message_auto_subscribe_notify_recruitment(self, users_per_task):
        # Utility method to send assignation notification upon writing/creation.
        if self.stage_id.name=="Interview" and self.check_pass_interview==False:
            template = 'hr_recruitment_application_update.confirm_cv_message'
            subject_template = "Confirm CV for Applicant"
        elif self.stage_id.name=="Interview" and self.check_pass_interview==True:
            template = 'hr_recruitment_application_update.pass_interview_message'
            subject_template = "Pass Interview"
        elif self.stage_id.name=="Initial Qualification":
            template = 'hr_recruitment_application_update.new_application_message'
            subject_template = "Create Application"
        elif self.stage_id.name=="Confirm CV":
            template = 'hr_recruitment_application_update.hearing_cv_application_message'
            subject_template = "Hearing CV"
        else:
            template = ''
            subject_template = ""

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
                values.update(assignee_name=user.sudo().name)
                assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
                assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
                task.message_notify(
                    subject=_('%s : %s', subject_template, task.display_name),
                    body=assignation_msg,
                    partner_ids = self.env['res.users'].search([('employee_ids.id','=',user.id)]).partner_id.ids,
                    record_name=task.display_name,
                    email_layout_xmlid='mail.mail_notification_light',
                    model_description=task_model_description,
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