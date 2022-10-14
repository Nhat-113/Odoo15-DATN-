from email.policy import default
from odoo import api, fields, models, _


class HrRequestOvertimeStage(models.Model):
    _name = "hr.request.overtime.stage"
    _description = "Timesheet Request Overtime Stages"
    _order = 'sequence'

    name = fields.Char("Stage Name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")


class HrRequestOverTime(models.Model):
    _name = "hr.request.overtime"

    _description = "Hr Request Overtime"
    _order = "id DESC"

    project_id = fields.Many2one('project.project', string="Project", required=True, domain="[('company_id', '=', company_id)]", tracking=True)
    start_date = fields.Date(string="Start date", required=False, tracking=True, store=True)
    end_date = fields.Date(string="End date", required=False, tracking=True, store=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company, tracking=True)
    description = fields.Text(string="Description", tracking=True)
    stage_id = fields.Many2one('hr.request.overtime.stage', 'Stage', ondelete='restrict', tracking=True,
                            # compute='_compute_stage', 
                            store=True, readonly=False,
                            # domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            # group_expand='_read_group_stage_ids'
                            )

    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Invisible Refuse Button', default=True)
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="All members has been assigned to the project", tracking=True)

    booking_overtime = fields.One2many('hr.booking.overtime', 'request_overtime_id', string='Booking Overtime')


    def archive_request_overtime(self):
        print('-------------------------------------')