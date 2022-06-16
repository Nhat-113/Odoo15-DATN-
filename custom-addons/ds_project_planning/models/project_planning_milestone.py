# -*- coding: utf-8 -*-

from cmath import phase
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
    _description = "Milestone in the Phase of Project"
    _order = "sequence,id"
    _rec_name = "name"

    def _get_default_project_id(self):
        return self.env.context.get('default_project_id') or self.env.context.get('active_id')

    def _get_default_phase_id(self):
        return self.env.context.get('default_phase_id')

    sequence = fields.Integer()
    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True, default=_get_default_project_id)
    pm_user_id = fields.Many2one(
        related='project_id.user_id', readonly=True, store=True)
    phase_id = fields.Many2one(
        'project.planning.phase', string='Phase', required=True, ondelete="cascade", help="Project Phase", default=_get_default_phase_id)
    start_date_phase = fields.Date(
        readonly=True, related='phase_id.start_date')
    end_date_phase = fields.Date(
        readonly=True, related='phase_id.end_date')
    name = fields.Char("Milestone name", required=True)
    type = fields.Char("Type", required=True, default="milestone")
    milestone_date = fields.Date(string='Milestone Date', required=True, help="Date of the milestone",
                                     default=date.today())
    description = fields.Html("Description")

    _sql_constraints = [
        ('name_uniq', 'unique (phase_id, name)', "Milestone name already exists!"),
    ]

    def _check_date(self):
        for milestone in self:
            if milestone.milestone_date and milestone.phase_id:
                if milestone.milestone_date > milestone.phase_id.end_date \
                        or milestone.milestone_date < milestone.phase_id.start_date:
                    raise ValidationError(_(
                        'Milestone date must be inside the (%(phase)s) phase.', phase=milestone.phase_id.name
                    ))

    @api.constrains('milestone_date')
    def _check_milestone_date(self):
        return self._check_date()

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id:
            if self.env.context.get('default_phase_id'):
                return

            phase_ids = self.env['project.planning.phase'].search(
                [('project_id', '=', self.project_id.id)])
            if phase_ids:
                self.phase_id = phase_ids[0].id
            else:
                raise UserError(
                    _('There is no phase in project "%(project)s", please create one!', project=self.project_id.name))
        else:
            self.phase_id = False

    # @api.onchange('milestone_date')
    def _validate_milestone_date(self):
        self._check_date()

    def write(self, vals):
        res = super(PlanningMilestone, self).write(vals)
        if self.milestone_date >= self.phase_id.start_date and self.milestone_date <= self.phase_id.end_date:
            return res
        else:
            raise UserError(
                _('The milestone date is invalid in the date range of the "%(phase)s" phase!', phase=self.phase_id.name))

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
