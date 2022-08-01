from datetime import date
import json
from random import randint

from odoo import models, fields, api
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
            3: 'yellow',
            4: 'lightblue',
            5: 'darkpurple',
            6: 'salmonpink',
            7: 'mediumblue',
            8: 'darkblue',
            9: 'fuchsia',
            10: 'green',
            11: 'purple'
        }
        return switcher.get(i, "Red")

    def _check_user_readonly(self):
        if self.env.user.has_group('project.group_project_manager') == True or\
                self.env.user.id == self.project_id.user_id.id or self.create_uid.id == self.env.user.id:
            self.is_readonly = False
        else:
            self.is_readonly = True

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

    @api.constrains('status', 'timesheet_ids')
    def _check_timesheet(self):
        if self.status.name == 'Done' or self.status.name == 'Closed' and self.issues_type.name == 'Task':
            if len(self.timesheet_ids) == 0:
                raise UserError(
                    'Time Sheet field cannot be left blank')
            elif self.planned_hours == 0.0:
                raise UserError(
                    'Initially Planned Hours field cannot be left blank')
            if self.progress_input != 100:
                raise UserError(
                    'Required when status Done or Closed, progress = 100%')

    @api.constrains('status')
    def _check_task_score(self):
        if self.status.name == 'Done':
            if self.task_score == '0':
                raise UserError(
                    'When the status is Done, you must score the task.')


    @api.constrains('progress_input')
    def _check_progress(self):
        if self.progress_input < 0 or self.progress_input > 100:
            raise UserError('Progress must be between 0 and 100%')
        elif self.status.name == 'Done' or self.status.name == 'Closed' and self.issues_type.name == 'Task':
            if self.progress_input != 100:
                raise UserError(
                    'Required when status Done or Closed, progress = 100%')

    @api.constrains('progress_input', 'timesheet_ids')
    def _check_timesheet_progress(self):
        if self.progress_input > 0:
            if len(self.timesheet_ids) == 0:
                raise UserError('Please update your timesheet.')
        if len(self.timesheet_ids) > 0:
            if self.progress_input == 0:
                raise UserError('Please update current progress.')

    @api.constrains('timesheet_ids')
    def _check_hours_spent(self):
        if len(self.timesheet_ids) > 0:
            for ts in self.timesheet_ids:
                if ts.unit_amount <= 0:
                    raise UserError(
                        'Required Hours Spent > 0')

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
        action['display_name'] = self.name
        return action

    @api.model
    def update_status(self):
        projects = self.env['project.project'].search([('active', '=', True)])
        for project in projects:
            task_all = self.env['project.task'].search_count(['&',('project_id', '=', project.id),('issues_type','=',1), ('status','!=',7)])
            task_out_of_date = self.env['project.task'].search_count(['&',('project_id', '=', project.id),('issues_type','=',1),('status','not in',[6,7]),('date_end','<',date.today())])
            if task_all > 0 and task_out_of_date/task_all >= 0.1 and project.last_update_status not in ['off_track', 'on_hold']:
                project.write({'last_update_status': 'at_risk'})

        return True

    @api.depends('planning_calendar_resources')
    def _compute_employee_id_domain(self):
        for project in self:
            user_ids = [
                user.id for user in project.planning_calendar_resources.employee_id]
            user_ids.append(self.env.user.employee_id.id)
            project.employee_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    
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
    