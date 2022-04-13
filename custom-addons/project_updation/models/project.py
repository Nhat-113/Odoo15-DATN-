from asyncore import write
import json
from random import randint

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class TaskStatus(models.Model):
    _name = "project.task.status"
    _description = "Task Status"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Name', required=True)
    color = fields.Char(string='Color')

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
    status = fields.Many2many('project.task.status', string='Status')

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

    issues_type = fields.Many2one('project.issues.type',
                                  string='Issues Type', required=True)
    icon_path = fields.Html('Issues Type', related='issues_type.icon_path')
    icon = fields.Image('Issues Type', related='issues_type.icon')
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
    status = fields.Many2one('project.task.status', string="Status")
    status_id_domain = fields.Char(
        compute='_get_status_id_domain',
        readonly=True,
        store=False
    )

    # @api.onchange('issues_type')
    # def m2mtom2o(self):
    #     if len(self.issues_type.status) > 0:
    #         self.status_selection = False
    #         for stt in self.issues_type.status:
    #             self.write({'status_selection': [(6, 0, [stt.id])]})

    @api.depends('issues_type')
    def _get_status_id_domain(self):
        status_ids = self.issues_type.status.ids
        for rec in self:
            rec.status_id_domain = json.dumps(
                [('id', 'in', status_ids)]
            )

    @api.constrains('status')
    def _check_timesheet(self):
        if self.status.name == 'Done':
            if len(self.timesheet_ids) == 0 or self.planned_hours == 0.0:
                raise UserError(
                    'Time Sheet field and Initially Planned Hours field cannot be left blank')

        if self.status.name == 'Closed':
            if len(self.timesheet_ids) == 0 or self.planned_hours == 0.0:
                raise UserError(
                    'Time Sheet field and Initially Planned Hours field cannot be left blank')
            else:
                self.progress = 100.0
        elif self.status.name != 'Closed':
            if self.planned_hours == 0.0:
                self.progress = 0
            else:
                self.progress = (self.effective_hours / self.planned_hours) * 100

    @api.onchange('status')
    def _set_progress(self):
        if self.status.name == 'Closed':
            self.progress = 100.0
        elif self.status.name != 'Closed':
            if self.planned_hours == 0.0:
                self.progress = 0
            self.progress = (self.effective_hours / self.planned_hours) * 100


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
