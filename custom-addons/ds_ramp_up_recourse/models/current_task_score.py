from datetime import date
from email.policy import default
from odoo import fields, models, api
from odoo import _

class ProjectTask(models.Model):
    _inherit = "project.task"
    _name  ="project.task" 

    reason_reject = fields.Char(string="Reason Refuse", help="Type Reason Reject Why Reject Task Score", readonly=False, tracking=True)
    status_task_score = fields.Selection([
    ('draft', 'To Approve'),
    ('confirm', 'Approved'),
    ('refuse', 'Refused'),
    ], default='draft', compute="reject_task_score", readonly=False, store=True, tracking=True)

    def _check_readonly(self):
        if self.env.user.has_group('ds_ramp_up_recourse.group_task_score_pm') == True:
            for task in self:
                task.read_only_reason_refuse = True
        else:
            for task in self:
                task.read_only_reason_refuse = False
    #count all bugs of task when install 
    def _default_search_count_bug_of_task_v2(self):
        bug_not_fix = self.env['project.task.status'].search([('name', '=' , 'Not Fixed')]).id
        count_bug_all_project = self.env['project.task'].search([])
        for task in count_bug_all_project:
            my_bug = self.env['project.task'].search([('task_id', '=', task.id), ('status', '!=',  bug_not_fix)])
            task.search_count_bug_of_task_update = len(my_bug)

    search_count_bug_of_task_update = fields.Integer(default=_default_search_count_bug_of_task_v2, store=True)

    read_only_reason_refuse = fields.Boolean(compute=_check_readonly, store=False)

    invisible_type_is_task = fields.Boolean(compute='_check_issue_type')
    
    @api.depends('issues_type')
    def _check_issue_type(self):
        if self.issues_type.name != 'Bug':
            self.task_id = False

        if self.issues_type.name == 'Bug':
            self.invisible_type_is_task = True
        else:
            self.invisible_type_is_task = False
   
    def _check_status_taskscore(self):
        for item in self: 
            if item.status_task_score == 'confirm':
               item.readonly_task_score = False
            else:
               item.readonly_task_score = True

    readonly_task_score = fields.Boolean(compute=_check_status_taskscore)

    def _default_count_time_sheet(self):
        timesheet_task = self.env['project.task'].search([])
        for record in timesheet_task: 
            record.count_time_sheets = len(record.timesheet_ids.ids)
 
    count_time_sheets = fields.Integer(store=True, default=_default_count_time_sheet, compute='_compute_timesheet_ids')
    
    @api.depends("timesheet_ids")
    def _compute_timesheet_ids(self):
        for item in self:
            item.count_time_sheets = len(item.timesheet_ids.ids)
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
        
    def open_task_detail(self):
        return {
            "name": _("Open Task"),
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "views": [[False, "form"]],
            "view_mode": 'form',
            "target": "new",
            'res_id': self.id
        }
    
    # count bugs of task  when created new bug
    @api.model
    def create(self, vals):
        bug_not_fix = self.env['project.task.status'].search([('name', '=' , 'Not Fixed')]).id
        issues_type = self.env['project.issues.type'].search([('name', '=' , 'Bug')]).id

        if vals['issues_type'] ==  issues_type:
            if 'task_id' in vals :
                find_task = self.env['project.task'].search([('id', '=', vals['task_id'])])
                count_bug = find_task.search_count_bug_of_task_update
                if vals['status'] != bug_not_fix:
                    find_task.write({'search_count_bug_of_task_update' : count_bug + 1})
        return super(ProjectTask, self).create(vals)

    # count bugs of task  when updated for isssue
    def write(self, vals):
        bug_not_fix = self.env['project.task.status'].search([('name', '=' , 'Not Fixed')]).id
        find_task_before = self.env['project.task'].search([('id', '=', self.task_id.id)])
        count_bug_task_before = find_task_before.search_count_bug_of_task_update
        if 'task_id' in vals: 

            if count_bug_task_before > 0:
                find_task_before.write({'search_count_bug_of_task_update' : count_bug_task_before - 1})

            find_task = self.env['project.task'].search([('id', '=', vals['task_id'])])
            count_bug = find_task.search_count_bug_of_task_update
            if  self.status != bug_not_fix :
                find_task.write({'search_count_bug_of_task_update' : count_bug + 1 }) 
        # when change  status to  not fixed 
        elif 'status' in vals:
            if vals['status'] == bug_not_fix:
                if count_bug_task_before > 0:
                    find_task_before.write({'search_count_bug_of_task_update' : count_bug_task_before - 1})
            elif self.status.id == bug_not_fix and vals['status'] != bug_not_fix:
                find_task_before.write({'search_count_bug_of_task_update' : count_bug_task_before + 1})
        res = super(ProjectTask, self).write(vals)
        return res

    #count bugs of task when deleted bug 
    def unlink(self):
        for record in self:
            bug_not_fix = self.env['project.task.status'].search([('name', '=' , 'Not Fixed')]).id
            find_task = self.env['project.task'].search([('id', '=',  self.task_id.id)])
            count_bug = find_task.search_count_bug_of_task_update
            if self.status.id != bug_not_fix:
                find_task.write({'search_count_bug_of_task_update' : count_bug - 1 })
        return super(ProjectTask, self).unlink()

    #thuat toan dung ma k update
    # @api.constrains('status')
    # def count_bug_of_task(self):
    #     for task in self:
    #         if  task.status.name == 'Not Fixed':
    #             count_bug_before = task.task_id.search_count_bug_of_task_upd
    #             task.write({'search_count_bug_of_task_upd': count_bug_before - 1})

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


