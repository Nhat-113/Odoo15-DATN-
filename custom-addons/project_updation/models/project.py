import calendar
from datetime import date
import json
from random import randint

from odoo import models, fields, api, _
from odoo.exceptions import UserError

STATUS_COLOR = {
    'on_track': 20,  # green / success
    'at_risk': 2,  # orange
    'off_track': 23,  # red / danger
    'on_hold': 4,
    'missing_resource':11,  # light blue
    False: 0,  # default grey -- for studio
}

class TaskStatus(models.Model):
    _name = "project.task.status"
    _description = "Task Status"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Name', required=True)
    color = fields.Integer(string='Color', default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name_status)', "Status name already exists!"),
    ]


class IssuesType(models.Model):
    _name = "project.issues.type"
    _description = "Issues Type"

    name = fields.Char(string='Name', required=True)
    description_issues = fields.Html(string='Description Issues')
    icon = fields.Binary(name='Icon', store=True, attachment=True)
    icon_path = fields.Html('Icon', compute='_get_img_html')
    status = fields.Many2many('project.task.status', string='Status Issues')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Issues type name already exists!"),
    ]

    def _get_img_html(self):

        for elem in self:
            domain = [
                ('res_model', '=', 'project.issues.type'),
                ('res_field', '=', 'icon'),
                ('res_id', '=', elem.id)
            ]
            att_id = self.env['ir.attachment'].sudo().search(domain).id
            if att_id:
                img_url = '/web/content/%s' % att_id
            else:
                img_url = '/project_updation/static/img/author_avatar.png'
            elem.icon_path = '<img src="%s"/>' % img_url


class Task(models.Model):
    _inherit = 'project.task'
    _order = 'create_date desc'

    issues_type = fields.Many2one('project.issues.type',
                                  string='Type', required=True, tracking=True)
    icon_path = fields.Html('Type Icon', related='issues_type.icon_path')
    icon = fields.Image('Type Icon', related='issues_type.icon')
    priority_type = fields.Selection([
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Priority Type', index=True, copy=False, default='low', tracking=True)
    create_date = fields.Datetime("Create Date", readonly=True, index=True)
    write_date = fields.Datetime("Update Date", readonly=True, index=True)

    complex = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Complex', index=True, copy=False, default='low', tracking=True)

    task_score = fields.Selection([
        ('0', 'Nothing'),
        ('1', '1 star (Cannot complete tasks and keep the deadlines)'),
        ('2', '2 stars (Can complete tasks and keep the deadlines, but quality is not so good)'),
        ('3', '3 stars (Can complete tasks and keep the deadlines, quality is pretty OK without any serious issues)'),
        ('4', '4 stars (Can complete the tasks ahead of time with a good quality)'),
        ('5', '5 stars (Can complete the tasks ahead of time with a very good quality, as well to support other members effectively)'),
    ], default='0', index=True, string="Task Score", tracking=True)
    status = fields.Many2one('project.task.status',
                             string="Status Task", tracking=True)
    status_id_domain = fields.Char(
        compute='_get_status_id_domain',
        readonly=True,
        store=False
    )
    is_readonly = fields.Boolean(compute='_check_user_readonly')
    progress_input = fields.Integer(string='Progress (%)', tracking=True)
    status_color = fields.Char(compute='_get_status_color', store=True)
    partner_id = fields.Many2one('res.partner',
        string='Customer',
        compute='_compute_partner_id', recursive=True, store=True, readonly=False, tracking=True,
        domain="[('is_company','=','true')]")
    task_id = fields.Many2one(
        'project.task', 'Bug of Task', store=True, readonly=False)

    @api.onchange('status')
    def set_progerss(self):
        for task in self:
            if task.status.name == 'Done':
                task.progress_input = 100
                task.date_deadline = date.today()

    def unlink(self):
        for task in self:
            if self.env.user.id not in task.user_ids.ids and self.env.user.has_group('ds_project_planning.group_project_pm') == False\
                and self.env.user.has_group('project.group_project_manager') == False:
               raise UserError("Do not delete other people's tasks, issues, QA.")
        return super().unlink()

    @api.depends('status')
    def _get_status_color(self):
        for color in self:
            color.status_color = color._color(color.status.color)

    def _color(self, i):
        switcher = {
            1: 'red',
            2: 'orange',
            3: 'orange',
            4: 'lightblue',
            5: 'green',
            6: 'fuchsia',
            7: 'purple',
            8: 'darkblue',
            9: 'fuchsia',
            10: 'green',
            11: 'purple'
        }
        return switcher.get(i, "Red")

    def _check_user_readonly(self):
        if self.env.user.has_group('project.group_project_manager') == True or self.env.user.has_group('ds_project_planning.group_project_team_leader') == True or\
                self.env.user.id == self.project_id.user_id.id or self.create_uid.id == self.env.user.id:
            self.is_readonly = False
        else:
            self.is_readonly = True

    @api.model
    def default_get(self, fields):
        id_issue_type_task = self.env['project.issues.type'].search([('name', '=' , 'Task')]).id
        result = super(Task, self).default_get(fields)
        result.update({
            'issues_type': id_issue_type_task 
        })
        return result

    @api.onchange('planned_hours')
    def _check_planned_hours(self):
        if self.planned_hours < 0:
            raise UserError('Required field Initial Planned Hours > 0')

    @api.depends('issues_type')
    def _get_status_id_domain(self):
        status_ids = self.issues_type.status.ids
        for rec in self:
            rec.status_id_domain = json.dumps(
                [('id', 'in', status_ids)]
            )

    @api.onchange('issues_type')
    def _get_first_status(self):
        if self.issues_type.status:
            self.status = self.issues_type.status[0]

    @api.constrains('status', 'timesheet_ids', 'child_ids')
    def _check_timesheet(self):
        for item in self: 
            if item.status.name == 'Done' and item.issues_type.name == 'Task':
                total_sub_task = self.env['project.task'].search_count([('parent_id', '=', self.id)])
                total_sub_task_done = 0
                for child_task in item.child_ids:
                    if child_task.status.name == 'Done':
                            total_sub_task_done += 1
                if total_sub_task != total_sub_task_done:
                    raise UserError(
                    'Sub Tasks must be completed when changing the status of the parent task!')

                if len(item.timesheet_ids) == 0 and total_sub_task == 0:
                    raise UserError(
                        'Time Sheet field cannot be left blank')
                elif item.planned_hours == 0.0:
                    raise UserError(
                        'Initially Planned Hours field cannot be left blank')
                if item.progress_input != 100:
                    raise UserError(
                        'Required when status Done or Closed, progress = 100%')
                if  item.task_score == '0':
                    raise UserError(
                        'When the status is Done, you must score the task.')
    # @api.constrains('status')
    # def _check_task_score(self):
    #     for item in self:
    #         if item.status.name == 'Done' and item.task_score == '0':
    #             raise UserError(
    #                 'When the status is Done, you must score the task.')


    @api.constrains('progress_input')
    def _check_progress(self):
        for item in self: 
            if item.progress_input < 0 or item.progress_input > 100:
                raise UserError('Progress must be between 0 and 100%')

    @api.constrains('progress_input', 'timesheet_ids')
    def _check_timesheet_progress(self):
        total_sub_task = self.env['project.task'].search_count([('parent_id', '=', self.id)])
        for item in self :
            if len(item.timesheet_ids) == 0 and item.progress_input > 0 and total_sub_task == 0 :
                    raise UserError('Please update your timesheet.')
            if len(item.timesheet_ids) > 0 and  item.progress_input == 0 and total_sub_task == 0 :
                    raise UserError('Please update current progress.')
            # requied user input timesheet
            if len(self.timesheet_ids) > 0:
                for ts in item.timesheet_ids:
                    if ts.unit_amount <= 0:
                        raise UserError(
                            'Required Hours Spent > 0')
            # requied user input progress_input from 0 to 100 %
            if item.progress_input < 0 or item.progress_input > 100:
                raise UserError('Progress must be between 0 and 100%')
    # @api.constrains('timesheet_ids')
    # def _check_hours_spent(self):
    #     if len(self.timesheet_ids) > 0:
    #         for ts in self.timesheet_ids:
    #             if ts.unit_amount <= 0:
    #                 raise UserError(
    #                     'Required Hours Spent > 0')

    @api.constrains('project_id')
    def _check_project_id(self):
        if not self.project_id:
            raise UserError('Please chose project.')


class Project(models.Model):
    _inherit = 'project.project'

    # status = fields.Selection([
    #     ('Open', 'Open'),
    #     ('Processing', 'Processing'),
    #     ('Close', 'Close'),
    #     ('Pending', 'Pending'),
    # ], string='Status', index=True, copy=False, default='Open')

    status_color = fields.Char('Status', compute='_get_status')
    last_update_status = fields.Selection(selection=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('missing_resource','Missing Resource'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold')
    ], default='on_track', compute='_compute_last_update_status', store=True)
    last_update_color = fields.Integer(compute='_compute_last_update_color')
    employee_id_domain = fields.Char(
        compute="_compute_employee_id_domain",
        readonly=True,
        store=False,
    )
    project_type = fields.Many2one('project.type', string="Project Type", readonly=False, compute='_compute_project_type', store=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', auto_join=True, tracking=True, domain="[('is_company', '=', True)]")

    @api.depends('estimation_id', 'estimation_id.project_type_id')
    def _compute_project_type(self):
        for record in self:
            if record.estimation_id.project_type_id.id:
                record.project_type = record.estimation_id.project_type_id.id
            else:
                record.project_type = False

    @api.constrains('project_type')
    def _validation_project_type(self):
        for record in self:
            if record.estimation_id.project_type_id.id and record.project_type.id != record.estimation_id.project_type_id.id:
                raise UserError ('Project Type of Project does not match with Project Type of Estimation')


    @api.depends('last_update_status')
    def _compute_last_update_color(self):
        for project in self:
            project.last_update_color = STATUS_COLOR[project.last_update_status]

    def _get_status(self):

        for stt in self:
            stt.status_color = stt.status

    def _compute_issue_count(self):
        for project in self:
            project.issue_count = self.env['project.task'].search_count(['&', ('issues_type', '!=', 1), (
                'project_id', '=', project.id), ('display_project_id', '=', project.id), ('active', '=', True)])

    issue_count = fields.Integer(compute='_compute_issue_count')

    def action_view_issues(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_updation.act_project_project_2_project_issue_all') \
            .sudo().read()[0]
        action['display_name'] = 'Issues/'+str(self.name)
        return action

    @api.model
    def update_status(self):
        projects = self.env['project.project'].search([('active', '=', True)])
        id_status_done = self.env['project.task.status'].search([('name', '=', 'Done')]).id
        id_status_cancel = self.env['project.task.status'].search([('name', '=', 'Cancelled')]).id
        id_status_pending = self.env['project.task.status'].search([('name', '=', 'Pending')]).id
        id_type_task = self.env['project.issues.type'].search([('name', '=', 'Task')]).id
        for project in projects:
            task_expired = []
            task_all = self.env['project.task'].search_count(['&',('project_id', '=', project.id),('issues_type','=',id_type_task), ('status','not in',[id_status_done, id_status_cancel, id_status_pending])])
            task_out_of_date = self.env['project.task'].search(['&',('project_id', '=', project.id),('issues_type','=',id_type_task),('status','not in',[id_status_done,id_status_cancel,id_status_pending]),('date_end','<',date.today())])
            if task_all > 0:
                # nếu số task bị trễ >= 10%(0.1) thì sẽ send mail và chuyển status thành at_risk
                if len(task_out_of_date)/task_all >= 0.1 and project.last_update_status not in ['off_track', 'on_hold', 'missing_resource']:
                    for task_expire in task_out_of_date:
                        task_expired.append(str(task_expire.id))
                    # Send mail
                    template = 'project_updation.warning_task_late'
                    subject_template = '[Warning] Project'
                    self._send_message_auto_task_deadline(project, task_expired, template, subject_template)
                    project.write({'last_update_status': 'at_risk'})
                elif len(task_out_of_date)/task_all < 0.1 and project.last_update_status not in ['off_track', 'on_hold', 'on_track', 'missing_resource']:
                    project.write({'last_update_status': 'on_track'})
            else:
                project.write({'last_update_status': 'on_track'})

        return True

    @api.model
    def _send_message_auto_task_deadline(self, project, task_expired, template, subject_template):

        template_id = self.env['ir.model.data']._xmlid_to_res_id(template, raise_if_not_found=False)
        if not template_id:
            return
        view = self.env['ir.ui.view'].browse(template_id)
        task_model_description = self.env['ir.model']._get(self._name).display_name
        action_planning_id = self.env.ref('ds_project_planning.open_planning_task_all_on_gantt', raise_if_not_found=False).id
        action_project_id = self.env.ref('project.act_project_project_2_project_task_all', raise_if_not_found=False).id
        first_task = self.env['project.task'].search([('id', '=', int(task_expired[0]))])
        values = {
            'object': project,
            'task' : task_expired,
            'model_description': task_model_description,
            'view_planning': first_task._notify_get_action_link_custom_mtech('view', action_planning_id, project.id, 'dhx_gantt'),
            'view_project': first_task._notify_get_action_link_custom_mtech('view', action_project_id, project.id, 'kanban'),
        }
    
        assignation_msg = view._render(values, engine='ir.qweb', minimal_qcontext=True)
        assignation_msg = self.env['mail.render.mixin']._replace_local_links(assignation_msg)                 
        project.message_notify(
            subject = _('%s : %s', subject_template, str(project.name)+' late task'),
            body = assignation_msg,
            partner_ids = project.user_id.partner_id.ids,
            record_name = project.name,
            email_layout_xmlid = 'mail.mail_notification_light',
            model_description = task_model_description,
        )

    @api.depends('planning_calendar_resources')
    def _compute_employee_id_domain(self):
        for project in self:
            user_ids = [
                user.id for user in project.planning_calendar_resources.employee_id]
            user_ids.append(self.env.user.employee_id.id)
            project.employee_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    @api.constrains('date', 'date_start')
    def check_edit_time(self):
        for project in self:
            list_dates = []

            project_revenues = self.env['project.revenue.value'].search([('project_id', '=', project.id)])
            for project_revenue in project_revenues:
                list_dates.append(date(int(project_revenue.get_year), int(project_revenue.get_month), 1))
            
            project_expenses = self.env['project.expense.value'].search([('project_id', '=', project.id)])
            for project_expense in project_expenses:
                list_dates.append(project_expense.expense_date)

            if len(list_dates) > 0:
                date_firstly = min(list_dates)
                date_final = max(list_dates)

                if project.date_start > date_firstly or project.date < date_final:
                    raise UserError(_('Invalid time. Cannot set duration of project outside the time set in Company Expenses (%(start)s --> %(end)s).',
                                            start=date_firstly, end=date_final))


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    status = fields.Selection(selection=[
        ('on_track', 'On Track'),
        ('at_risk', 'At Risk'),
        ('missing_resource','Missing Resource'),
        ('off_track', 'Off Track'),
        ('on_hold', 'On Hold')       
    ], required=True, tracking=True)
    color = fields.Integer(compute='_compute_color')

    @api.depends('status')
    def _compute_color(self):
        for update in self:
            update.color = STATUS_COLOR[update.status]


class TimeSheet(models.Model):
    _inherit = 'account.analytic.line'

    employee_id_domain = fields.Char(
        related='project_id.employee_id_domain',
        readonly=True,
        store=False,
    )
    