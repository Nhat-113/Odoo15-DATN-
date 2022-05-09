import json
from random import randint

from odoo import models, fields, api
from odoo.exceptions import UserError
from collections import defaultdict


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
    _order= 'create_date desc'

    issues_type = fields.Many2one('project.issues.type',
                                  string='Type', required=True, tracking=True)
    icon_path = fields.Html('Type Icon', related='issues_type.icon_path')
    icon = fields.Image('Type Icon', related='issues_type.icon')
    priority_type = fields.Selection([
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Priority Type', index=True, copy=False, default='low')

    complex = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Complex', index=True, copy=False, default='low')

    task_score = fields.Selection([
        ('0', 'Nothing'),
        ('1', 'Very Bad'),
        ('2', 'Bad'),
        ('3', 'Normal'),
        ('4', 'Good'),
        ('5', 'Very Good'),
    ], default='0', index=True, string="Task Score", tracking=True)
    status = fields.Many2one('project.task.status', string="Status Task")
    status_id_domain = fields.Char(
        compute='_get_status_id_domain',
        readonly=True,
        store=False
    )
    is_readonly = fields.Boolean(compute='_check_user_readonly')
    progress_input = fields.Integer(string='Progress (%)')
    status_color = fields.Char(compute='_get_status_color', store=True)

    @api.depends('status')
    def _get_status_color(self):
        for color in self:
            color.status_color = color._color(color.status.color)


    def _color(self, i):
        switcher={
            1:'red',
            2:'orange',
            3:'yellow',
            4:'lightblue',
            5:'darkpurple',
            6:'salmonpink',
            7:'mediumblue', 
            8:'darkblue',
            9:'fuchsia',
            10:'green',
            11:'purple'
        }
        return switcher.get(i,"Red")


    def _check_user_readonly(self):
        if self.env.user.has_group('project.group_project_manager') == False or\
            self.env.user.id != self.project_id.user_id.id:
            self.is_readonly = True
        else:
            self.is_readonly = False

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
        if self.status.name == 'Done' or self.status.name == 'Closed':
            if len(self.timesheet_ids) == 0 or self.planned_hours == 0.0:
                raise UserError(
                    'Time Sheet field and Initially Planned Hours field cannot be left blank')
            if self.progress_input != 100:
                raise UserError(
                    'Required when status Done or Closed, progress = 100%')

    @api.constrains('progress_input')
    def _check_progress(self):
        if self.progress_input < 0 or self.progress_input > 100:
            raise UserError('Progress must be between 0 and 100%')
    
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

    status = fields.Selection([
        ('Open', 'Open'),
        ('Processing', 'Processing'),
        ('Close', 'Close'),
        ('Pending', 'Pending'),
    ], string='Status', index=True, copy=False, default='Open')

    status_color = fields.Char('Status', compute='_get_status')

    def _get_status(self):

        for stt in self:
            stt.status_color = stt.status

    def _compute_issue_count(self):
        for project in self:
            project.issue_count = self.env['project.task'].search_count(['&',('issues_type','!=',1),('project_id','=',project.id)])
    
    issue_count = fields.Integer(compute='_compute_issue_count')


    def action_view_issues(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_updation.act_project_project_2_project_issue_all') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action