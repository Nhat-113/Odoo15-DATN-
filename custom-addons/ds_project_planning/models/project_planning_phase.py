# -*- coding: utf-8 -*-

from asyncio import tasks
from re import S
from unicodedata import name
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time
from dateutil import relativedelta
from odoo.exceptions import ValidationError, UserError


class PlanningPhase(models.Model):
    """
    Describe Project Planning Phase in configuration.
    """
    _name = "project.planning.phase"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Planning for Phase of project"
    _order = "sequence,id"
    _rec_name = "name"

    def _get_default_project_id(self):
        return self.env.context.get('default_project_id') or self.env.context.get('active_id')

    sequence = fields.Integer()
    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True, default=_get_default_project_id)
    pm_user_id = fields.Many2one(
        related='project_id.user_id', readonly=True, store=True)
    project_tasks = fields.One2many(
        'project.task', 'phase_id', string='Tasks')
    name = fields.Char("Phase name", required=True)
    type = fields.Char("Type", required=True, default="phase")

    phase_duration = fields.Float('Phase duration', compute='_compute_phase_duration', store=True)

    start_date = fields.Datetime(string='Date Start', readonly=False, required=True, help="Start date of the phase",
                                 default=lambda self: fields.Datetime.to_string(
                                     datetime.today().replace(day=1, hour=0, minute=0, second=0)))
    end_date = fields.Datetime(
        string='Date End', readonly=False, required=True, help="End date of the phase", default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=31, hour=16, minute=59, second=59))[:19])
    description = fields.Html("Description")
    count_milestone = fields.Integer(
        string="Milestones", compute="_count_milestone_in_phase")
    tasks_count = fields.Integer(
        string="Tasks", compute="_count_task_in_phase")

    _sql_constraints = [
        ('name_uniq', 'unique (project_id, name)', "Phase name already exists!"),
    ]

    @api.depends('start_date', 'end_date')
    def _compute_phase_duration(self):
        for r in self:
            if r.start_date and r.end_date:
                elapsed_seconds = (r.end_date - r.start_date).total_seconds()
                seconds_in_day = 24 * 60 * 60
                r.phase_duration = elapsed_seconds / seconds_in_day
                r = r.with_context(ignore_onchange_phase_duration=True)

    def _check_dates(self):
        for phase in self:
            if phase.end_date and phase.start_date > phase.end_date:
                raise ValidationError(_(
                    'Phase "%(phase)s": start date (%(start)s) must be earlier than end date (%(end)s).',
                    phase=phase.name, start=phase.start_date, end=phase.end_date,
                ))

    @api.constrains('start_date', 'end_date')
    def _check_start_end(self):
        return self._validate_by_start_end()

    def get_phase_between(self, project, start_date, end_date):
        """
        @param project: recordset of project
        @param start_date: datetime field
        @param end_date: datetime field
        @return: returns all phases for the given project that need to be considered for the given dates
        """
        # a phase is valid if it ends between the given dates
        clause_1 = ['&', ('end_date', '<=', end_date),
                    ('end_date', '>=', start_date)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('start_date', '<=', end_date),
                    ('start_date', '>=', start_date)]
        # OR if it starts before the start_date and finish after the end_date
        clause_3 = ['&', ('start_date', '<=', start_date),
                    ('end_date', '>=', end_date)]
        clause_final = [('project_id', '=', project.id), ('id', '!=', self.id or self.id.origin),
                        '|', '|'] + clause_1 + clause_2 + clause_3

        return self.env['project.planning.phase'].search(clause_final)

    # @api.onchange('start_date', 'end_date')
    def _validate_by_start_end(self):
        self._check_dates()

        if self.project_id and self.start_date and self.end_date:
            # Validate if the current phase is considered to be in another phase
            considered_phases = self.get_phase_between(
                self.project_id, self.start_date, self.end_date)
            if considered_phases:
                raise UserError(
                    _('Date Start & Date End of the current Phase is considered to be in "%(phase)s" phase!', phase=considered_phases[0].name))

    def compute_tasks(self):
        if self.project_id and self.start_date and self.end_date:

            # tasks is valid if it ends between the given dates
            clause_1 = ['&', ('date_start', '>=', self.start_date),
                        ('date_end', '<=', self.end_date)]
            # OR if it finish between the given dates
            clause_2 = ['&', ('date_end', '>=', self.start_date),
                        ('date_end', '<=', self.end_date)]
            domain = [('project_id', '=', self.project_id.id),
                      '|'] + clause_1 + clause_2
            tasks = self.env['project.task'].search(domain)
            # self.write({'project_tasks': [(3, task.id, 0) for task in self.project_tasks.ids]})
            self.write({'project_tasks': [(6, 0, tasks.ids)]})

        return {}

    def _count_milestone_in_phase(self):
        for phase in self:
            num_milestone = self.env['project.planning.milestone'].search(
                ['&', ('project_id', '=', phase.project_id.id), ('phase_id', '=', phase.id)])
            phase.count_milestone = len(num_milestone)

    def _count_task_in_phase(self):
        for phase in self:
            num_tasks = self.env['project.task'].search(
                ['&', ('project_id', '=', phase.project_id.id), ('phase_id', '=', phase.id)])
            phase.tasks_count = len(num_tasks)

    @api.model
    def open_create_phase(self, project_id):
        # res = { 'type': 'ir.actions.client', 'tag': 'reload' } # reload the current page/url
        res = {
            "name": _("Create Phase"),
            "type": "ir.actions.act_window",
            "res_model": "project.planning.phase",
            "views": [[False, "form"]],
            "view_mode": 'form',
            # "target": "new",
            "context": {'default_project_id': project_id},
        }

        return res

    def open_create_milestone_form(self):
        return {
            "name": _("Create Milestone"),
            "type": "ir.actions.act_window",
            "res_model": "project.planning.milestone",
            "views": [[self.env.ref('ds_project_planning.view_form_project_milestone').id, "form"]],
            'target': 'new',
            "context": {'default_project_id': self.project_id.id, 'default_phase_id': self.id},
        }
