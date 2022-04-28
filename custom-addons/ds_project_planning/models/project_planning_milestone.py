# -*- coding: utf-8 -*-

from unicodedata import name
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time
from odoo.exceptions import ValidationError, UserError


class PlanningMilestone(models.Model):
    """
    Describe Project Planning Milestone in configuration.
    """
    _name = "project.planning.milestone"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Planning for Milestone of the Phase in the project"
    _order = "sequence,id"
    _rec_name = "name"

    def _get_default_project_id(self):
        return self.env.context.get('default_project_id') or self.env.context.get('active_id')

    sequence = fields.Integer()
    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True, default=_get_default_project_id)
    pm_user_id = fields.Many2one(related='project_id.user_id', readonly=True, store=True)
    phase_id = fields.Many2one(
        'project.planning.phase', string='Phase', required=True, ondelete="cascade", help="Project Phase")
    start_date_phase = fields.Datetime(
        readonly=True, related='phase_id.start_date')
    end_date_phase = fields.Datetime(
        readonly=True, related='phase_id.end_date')
    project_tasks = fields.One2many(
        'project.task', 'milestone_id', string='Tasks')
    name = fields.Char("Milestone name", required=True)
    type = fields.Char("Type", required=True, default="milestone")
    start_date = fields.Datetime(string='Date Start', readonly=False, required=True, help="Start date of the milestone",
                                 default=lambda self: fields.Date.to_string(
                                     date.today().replace(day=1)))
    end_date = fields.Datetime(
        string='Date End', readonly=False, required=True, help="End date of the milestone")
    description = fields.Html("Description")
    tasks_count = fields.Integer(
        string="Tasks", compute="_count_task_in_phase")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Milestone name already exists!"),
    ]

    def _check_dates(self):
        for milestone in self:
            if milestone.end_date and milestone.start_date > milestone.end_date:
                raise ValidationError(_(
                    'Milestone "%(milestone)s": start date (%(start)s) must be earlier than end date (%(end)s).',
                    milestone=milestone.name, start=milestone.start_date, end=milestone.end_date,
                ))

    @api.constrains('start_date', 'end_date')
    def _check_start_end(self):
        return self._check_dates()

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            phase_ids = self.env['project.planning.phase'].search(
                [('project_id', '=', self.project_id.id)])
            if phase_ids:
                self.phase_id = phase_ids[0].id
            else:
                raise UserError(
                    _('There is no phase in project "%(project)s", please create one!', project=self.project_id.name))
        else:
            self.phase_id = False

    def get_milestone_between(self, project, start_date, end_date):
        """
        @param project: recordset of project
        @param start_date: datetime field
        @param end_date: datetime field
        @return: returns all milestones in a phase for the given project that need to be considered for the given dates
        """
        # a milestone is valid if it ends between the given dates
        clause_1 = ['&', ('end_date', '<=', end_date),
                    ('end_date', '>=', start_date)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('start_date', '<=', end_date),
                    ('start_date', '>=', start_date)]
        # OR if it starts before the start_date and finish after the end_date
        clause_3 = ['&', ('start_date', '<=', start_date),
                    ('end_date', '>=', end_date)]
        clause_final = [('project_id', '=', project.id), ('id', '!=', self.id.origin),
                        '|', '|'] + clause_1 + clause_2 + clause_3

        return self.env['project.planning.milestone'].search(clause_final)

    @api.onchange('start_date', 'end_date')
    def _validate_by_start_end(self):
        self._check_dates()

        if self.project_id and self.start_date and self.end_date:
            # Validate if the current milestone is considered to be in another milestone
            considered_milestones = self.get_milestone_between(
                self.project_id, self.start_date, self.end_date)
            if considered_milestones:
                raise UserError(
                    _('Date Start & Date End of the current Milestone is considered to be in "%(milestone)s" milestone!', milestone=considered_milestones[0].name))

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

    def write(self, vals):
        res = super(PlanningMilestone, self).write(vals)
        if self.start_date >= self.phase_id.start_date and self.end_date <= self.phase_id.end_date:
            return res
        else:
            raise UserError(
                _('The start and end dates are invalid in the date range of the "%(phase)s" phase!', phase=self.phase_id.name))

    def _count_task_in_phase(self):
        for milestone in self:
            num_tasks = self.env['project.task'].search(
                ['&', ('project_id', '=', milestone.project_id.id), ('milestone_id', '=', milestone.id)])
            milestone.tasks_count = len(num_tasks)

    @api.model
    def open_create_milestone(self, project_id):
        return {
            "name": _("Create Milestone"),
            "type": "ir.actions.act_window",
            "res_model": "project.planning.milestone",
            "views": [[False, "form"]],
            "view_mode": 'form',
            # "target": "new",
            "context": {'default_project_id': project_id},
        }
