# -*- coding: utf-8 -*-
import datetime
import pandas as pd

from cmath import phase
from odoo import models, fields, api, _
from datetime import timedelta, datetime
import json

from odoo.exceptions import ValidationError

class ProjectTask(models.Model):
    _inherit = ['project.task']

    user_id_domain = fields.Char(
        related='project_id.user_id_domain',
        readonly=True,
        store=False,
    )
    phase_id = fields.Many2one(
        'project.planning.phase', string='Phase', required=False, help="Project Phase")
    milestone_id = fields.Many2one(
        'project.planning.milestone', string='Milestone', required=False, domain=[('phase_id', '=', phase_id)], help="Project Milestone")

    planned_duration = fields.Float('Duration', default=0, compute='_compute_planned_duration', inverse='_inverse_planned_duration', store=True, readonly=True)
    working_day = fields.Float('Working Day', default=0,compute='_compute_working_day', store=True, readonly=True)
    lag_time = fields.Integer('Lag Time')
    depending_task_ids = fields.One2many('project.depending.tasks', 'task_id')
    dependency_task_ids = fields.One2many(
        'project.depending.tasks', 'depending_task_id')
    links_serialized_json = fields.Char(
        'Serialized Links JSON', compute="compute_links_json")
    date_start = fields.Date('Start Date')
    date_end = fields.Date('End Date')
    user_readonly = fields.Boolean(compute='_check_user_readonly_date')
    
    recursive_dependency_task_ids = fields.Many2many(
        string='Recursive Dependencies',
        comodel_name='project.task',
        compute='_compute_recursive_dependency_task_ids'
    )
    # check_phase_required = fields.Boolean(default = True)

    def _check_user_readonly_date(self):
        if self.env.user.has_group('project.group_project_manager') == False and self.env.user.has_group('ds_project_planning.group_project_team_leader') == False\
            and self.env.user.has_group('ds_project_planning.group_project_pm') == False:
            self.user_readonly = True
        else:
            self.user_readonly = False

    # @api.model
    # def create(self, vals):
    #     # Lấy giá trị từ vals nếu có
    #     phase_id = vals.get('phase_id')
    #     date_start = datetime.strptime(vals.get('date_start'), '%Y-%m-%d').date() if vals.get('date_start') is not False else None
    #     date_end = datetime.strptime(vals.get('date_end'), '%Y-%m-%d').date() if vals.get('date_end') is not False else None

    #     if phase_id:
    #         phase = self.env['project.planning.phase'].browse(phase_id)
    #         if not date_start and not date_end:
    #             return super(ProjectTask, self).create(vals)
    #         elif date_start > phase.end_date or date_end < phase.start_date:
    #             raise ValidationError(
    #                 "Dates must be within the phase period from {start_date} to {end_date}. "
    #                 "Please choose different dates.".format(
    #                     start_date=phase.start_date.strftime('%d-%m-%Y'),
    #                     end_date=phase.end_date.strftime('%d-%m-%Y')
    #                 )
    #             )
        
    #     # Tiếp tục tạo bản ghi sau khi kiểm tra xong
    #     return super(ProjectTask, self).create(vals)

    # def write(self, vals):
        # Lấy các giá trị phase_id, date_start, và date_end từ vals nếu có
        # phase_id = vals.get('phase_id', self.phase_id.id)
        # date_start_vals = self._get_date_from_vals(vals, 'date_start')
        # date_end_vals = self._get_date_from_vals(vals, 'date_end')
        # date_start = date_start_vals if vals.get('date_start') else self.date_start
        # date_end = date_end_vals if vals.get('date_end')  else self.date_end

        # Kiểm tra điều kiện với phase_id và dates
        # if phase_id:
        #     phase = self.env['project.planning.phase'].browse(phase_id)
        #     if not date_start and not date_end:
                
        #         return super(ProjectTask, self).write(vals)
        #     if date_start > phase.end_date or date_end < phase.start_date:
        #         raise ValidationError(
        #             "Dates must be within the phase period from {start_date} to {end_date}. "
        #             "Please choose different dates.".format(
        #                 start_date=phase.start_date.strftime('%d-%m-%Y'),
        #                 end_date=phase.end_date.strftime('%d-%m-%Y')
        #             )
        #         )

        # if 'date_start' in vals or 'date_end' in vals: #date of task
        #     phase_ids = self._get_phase_ids(self, self.date_start, self.date_end)

        #     task_phase_id = phase_id
        #     if len(phase_ids) == 1:
        #         task_phase_id = phase_ids.id
        #     elif self.phase_id in phase_ids:
        #         task_phase_id = self.phase_id.id
        #     if vals.get('phase_id'):
        #         task_phase_id = vals.get('phase_id')
        #     vals['phase_id'] = task_phase_id
        # return super(ProjectTask, self).write(vals)

    # def _get_phase_ids(self, task, date_start, date_end):
    #     domain = [
    #         ('project_id', '=', task.project_id.id),
    #         '|', '|', 
    #         '&',
    #         ('start_date', '>', date_start), 
    #         ('start_date', '<=', date_end),
    #         '&',
    #         ('start_date', '<=', date_end), 
    #         ('end_date', '>=', date_end),
    #         '&',
    #         ('end_date', '>=', date_start), 
    #         ('end_date', '<=', date_end)
    #     ]
    #     return task.env['project.planning.phase'].search(domain)

    @api.depends('date_start', 'date_end')
    def _compute_planned_duration(self):
        for r in self:
            if r.date_start and r.date_end:
                # elapsed_seconds = (r.date_end - r.date_start + timedelta(days=1)).total_seconds()
                # seconds_in_day = 24 * 60 * 60
                # r.planned_duration = round(elapsed_seconds / seconds_in_day, 1)
                r.planned_duration = (r.date_end - r.date_start).days + 1
                r = r.with_context(ignore_onchange_planned_duration=True)
            elif not r.date_start or not r.date_end:
                r.planned_duration = 0
    @api.depends('date_start', 'date_end')
    def _compute_working_day(self):
        for r in self:
            if r.date_start and r.date_end:
                working_days = len(pd.bdate_range(r.date_start.strftime('%Y-%m-%d'),
                                                  r.date_end.strftime('%Y-%m-%d')))
                elapsed_seconds = working_days * 24 * 60 * 60
                seconds_in_day = 24 * 60 * 60
                r.working_day = round(elapsed_seconds / seconds_in_day, 1)
            elif not r.date_start or not r.date_end:
                r.working_day = 0

    # @api.onchange('date_start', 'date_end')
    # def _onchange_date_field(self):
    #     if self.date_start:
    #         phase_ids = self._get_phase_ids(self, self.date_start, self.date_end)
    #         if len(phase_ids) != 1:
    #             self.check_phase_required = False

    @api.onchange('planned_duration', 'date_start', 'date_end')
    def _inverse_planned_duration(self):
        for r in self:            
            if r.date_start and not r.env.context.get('ignore_onchange_planned_duration', False):
                if r.date_start and r.date_end and r.date_end < r.date_start  and  r.planned_duration <= 0.0:
                    r.date_start = r.date_end
                if r.planned_duration == 0.0:
                    r.planned_duration = 1
                # drag in mode zoom out follow week
                if r.date_start and r.date_end and  r.date_start == r.date_end and r.planned_duration <= 0 :
                    r.planned_duration = 1
                    r.date_end = r.date_start + timedelta(days=r.planned_duration - 1)
                if r.date_start and r.date_end and  r.date_start < r.date_end and r.planned_duration <= 0 :
                    r.planned_duration = 1
                    r.date_end = r.date_start + timedelta(days=r.planned_duration - 1)   
                r.date_end = r.date_start + timedelta(days=r.planned_duration - 1)
                # if r.working_day == 0:
                #     r.working_day = 1
                    

    @api.depends('dependency_task_ids')
    def _compute_recursive_dependency_task_ids(self):
        for task in self:
            task.recursive_dependency_task_ids = task.get_dependency_tasks(
                task, True,
            )

    @api.model
    def get_dependency_tasks(self, task, recursive=False):
        dependency_tasks = task.with_context(
            prefetch_fields=False,
        ).dependency_task_ids
        if recursive:
            for t in dependency_tasks:
                dependency_tasks |= self.get_dependency_tasks(t, recursive)
        return dependency_tasks

    def compute_links_json(self):
        for r in self:
            links = []
            r.links_serialized_json = '['
            for link in r.dependency_task_ids:
                json_obj = {
                    'id': link.id,
                    'source': link.task_id.id,
                    'target': link.depending_task_id.id,
                    'type': link.relation_type
                }
                links.append(json_obj)
            r.links_serialized_json = json.dumps(links)

    @api.constrains('date_start', 'date_end')
    def _check_start_end(self):
        for task in self:
            if task.date_start and task.date_end and task.date_start > task.date_end and task.planned_duration == 0:
                if (task.date_start - task.date_end).days > 1:
                    raise ValidationError(_(
                        'Task "%(task)s": start date (%(start)s) must be earlier than end date (%(end)s).',
                        task=task.name, start=task.date_start, end=task.date_end,
                    ))
                else:
                    task.planned_duration == 1
        # if self.date_end and not self.date_start:
        #     raise ValidationError("Please select a start date")
   
    # def _get_date_from_vals(self, vals, field_name):
    #     """
    #     Function to get date value from vals and convert it to date format.
    #     """
    #     if vals.get(field_name):
    #         if isinstance(vals[field_name], str):
    #             return datetime.strptime(vals[field_name], '%Y-%m-%d').date()
    #         else:
    #             return vals[field_name]
    #     return None

    def update_date_end(self, stage_id):
        return {}

    @api.model
    def open_create_task(self, project_id):
        return {
            "name": _("Create Task"),
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "views": [[False, "form"]],
            "view_mode": 'form',
            # "target": "new",
            "context": {'default_project_id': project_id, 'default_issues_type': 1},
        }


class DependingTasks(models.Model):
    _name = "project.depending.tasks"
    _description = "Tasks Dependency (m2m)"

    task_id = fields.Many2one('project.task', required=True)
    project_id = fields.Many2one(
        'project.project', compute='_compute_project_id', string='Project')
    depending_task_id = fields.Many2one('project.task', required=True)
    relation_type = fields.Selection([
        ("0", "Finish to Start"),
        ("1", "Start to Start"),
        ("2", "Finish to Finish"),
        ("3", "Start to Finish")
    ], default="0", required=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done')], default='draft')

    _sql_constraints = [
        ('task_relation_unique', 'unique(task_id, depending_task_id)',
         'Two tasks can have only one relation!'),
    ]
    
    @api.depends('task_id')
    def _compute_task_id_domain(self):
        for task in self:
            id_bug = self.env['project.issues.type'].search([('name', '=', 'Task')]).id
            if len(task.depending_task_id.ids) > 0:
                task.task_id_domain = json.dumps(
                    [('project_id', '=', task.project_id.id), ('id', '!=', task.depending_task_id.ids[0]), ('issues_type', '=', id_bug)]
                )
            elif len(task.task_id.ids) > 0:
                task.task_id_domain = json.dumps(
                    [('project_id', '=', task.project_id.id), ('id', '!=', task.task_id.ids[0]), ('issues_type', '=', id_bug)]
                )
            else:
                task.task_id_domain = json.dumps(
                    [('project_id', '=', task.project_id.id), ('issues_type', '=', id_bug)]
                )

    task_id_domain = fields.Char(
        compute="_compute_task_id_domain",
        readonly=True,
        store=False,
    )


    @api.onchange('task_id', 'depending_task_id')
    def _compute_project_id(self):
        for r in self:
            if r.task_id:
                r.project_id = r.task_id.project_id
            elif r.depending_task_id:
                r.project_id = r.depending_task_id.project_id
