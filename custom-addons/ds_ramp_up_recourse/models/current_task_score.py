from datetime import date
from email.policy import default
from odoo import fields, models, api
from odoo import _


class CurrentTaskScore(models.Model):
    _name = "current.task.score"
    _description = "Current Task Score"
    _auto = False

    id = fields.Many2one('hr.employee', string="ID", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    name = fields.Char(string="Employee Name", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    job_id = fields.Many2one('hr.job', string="Job Position", readonly=True)
    parent_id = fields.Many2one('hr.employee', string="Parent ID", readonly=True)
    company_id = fields.Many2one('res.company', string="Company ID", readonly=True)
    task_score_avg = fields.Float(string='Task Score', digits=(12, 1), readonly=True)


    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                (
                    SELECT
                        emp.id,
                        emp.id as employee_id,
                        emp.name,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id,
                        emp.company_id,
						SUM(project_task.task_score::decimal)/COUNT(project_task.task_score) as task_score_avg
						
                    FROM (
                        SELECT
                            id,
                            name,
                            department_id,
                            job_id,
                            parent_id,
                            company_id,
							user_id
                        FROM
                            hr_employee
                        ) as emp
                    LEFT JOIN 	
                        project_task_user_rel ab
                            ON ab.user_id = emp.user_id
					LEFT JOIN
                        project_task
                            ON ab.task_id = project_task.id
					WHERE
						project_task.date_start >= CONCAT(to_char(date_part('year', CURRENT_DATE), '9999'), '-01-01')::date
						AND project_task.date_end <= CONCAT(to_char(date_part('year', CURRENT_DATE), '9999'), '-12-31')::date
						AND project_task.issues_type = 1
						AND project_task.task_score != '0'
                        AND project_task.count_time_sheets > 0
					GROUP BY
						emp.id,
                        emp.name,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id,
                        emp.company_id
                )
            )
        """ % (self._table))

    def current_task_score_action(self):
        user_id = self.env['hr.employee'].search([('id', '=', self.id)]).user_id.id
        name_view = self.env['hr.employee'].search([('id', '=', self.id)]).name
        action = {
            "name": name_view,
            "type": "ir.actions.act_window",
            'search_view_id': [self.env.ref('ds_ramp_up_recourse.task_score_search').id, 'search'],
            "res_model": "project.task",
            "views": [[self.env.ref('ds_ramp_up_recourse.task_score_view_tree').id, "tree"]],
            "domain": [('user_ids', 'in', user_id), ('issues_type', '=', 1), ('count_time_sheets', '>', 0),
                ('date_start', '>=', date(date.today().year, 1, 1)), 
                ('date_end', '<=', date(date.today().year, 12, 31)), ('task_score', 'not in', ['0'])]
        }
        return action


class ProjectTask(models.Model):
    _inherit = "project.task"
    _name  ="project.task" 

    def _search_count_bug_of_task(self):
        for task in self:
            my_bug = self.env['project.task'].search([('task_id', '=', task.id)])
            task.search_count_bug_of_task = len(my_bug)
            
    def _check_readonly(self):
        if self.env.user.has_group('ds_ramp_up_recourse.group_task_score_pm') == True and self.env.user.has_group('ds_ramp_up_recourse.group_task_score_admin') == False:
            for task in self:
                task.read_only_reason_refuse = True
        else:
            for task in self:
                task.read_only_reason_refuse = False

    reason_reject = fields.Char(string="Reason Refuse", help="Type Reason Reject Why Reject Task Score", readonly=False, tracking=True)
    search_count_bug_of_task = fields.Integer(compute=_search_count_bug_of_task)

    read_only_reason_refuse = fields.Boolean(compute=_check_readonly, store=False)

    def approve_task_score(self):
        for record in self:
            record.status_task_score = 'confirm'
            # employee_id = record.user_ids

    @api.depends('reason_reject')
    def reject_task_score(self):
        for task in self:
            if task.reason_reject != False:
                for emp in task.user_ids:
                    task.status_task_score = 'refuse'
            else:
                task.status_task_score = 'draft'
        
    # def send_mail_reject_task_score(self, emp):
    #     IrConfigParameter = self.env["ir.config_parameter"].sudo()
    #     template_env = self.env["mail.template"]
    #     send_employee = True

    #     # Send mail approve to employee
    #     if send_employee:
    #         domain = [
    #             ("id", "=", emp),
    #         ]
    #         emp_template_id = IrConfigParameter.get_param(
    #             "employee.emp_approve_template_id"
    #         )
    #         if emp_template_id:
    #             template_id = template_env.sudo().browse(int(emp_template_id))
    #             for employee in self.env["hr.employee"].search(domain):
    #                 template_id.send_mail(employee.id)
    
    @api.onchange('reason_reject')
    def send_mail(self):
        for task in self:
            if task.reason_reject != '':
                self._task_message_auto_subscribe_notify_refuse_task_score({task: task.user_ids - self.env.user for task in task})
    #function send mail refuse task score 
    @api.model
    def _task_message_auto_subscribe_notify_refuse_task_score(self, users_per_task):
        # Utility method to send assignation notification upon writing/creation.
        template_id = self.env['ir.model.data']._xmlid_to_res_id('ds_ramp_up_recourse.project_message_user_refuse', raise_if_not_found=False)
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
                    subject=_('You have been refused task score of task has name %s', task.display_name),
                    body=assignation_msg,
                    partner_ids=user.partner_id.ids,
                    record_name=task.display_name,
                    email_layout_xmlid='mail.mail_notification_light',
                    model_description=task_model_description,
                )
