from odoo import api, fields, models, _


class HrRequestOvertimeStage(models.Model):
    _name = "hr.request.overtime.stage"
    _description = "Timesheet Request Overtime Stages"
    _order = 'sequence'

    name = fields.Char("Stage Name", required=True, translate=True)
    sequence = fields.Integer(
        "Sequence", default=10,
        help="Gives the sequence order when displaying a list of stages.")
    confirm_stage = fields.Boolean('Confirm Stage',
        help="...")
    

class HrRequestOverTime(models.Model):
    _name = "hr.request.overtime"

    _description = "Hr Request Overtime"
    _order = "id DESC"

    @api.model
    def _get_default_stage_id(self):
        return self.env['hr.request.overtime.stage'].search([], limit=1).id

    name = fields.Char("Subject", required=True)
    project_id = fields.Many2one('project.project', string="Project", required=True, tracking=True)
    start_date = fields.Date(string="Start Date", required=False, tracking=True, store=True)
    end_date = fields.Date(string="End Date", required=False, tracking=True, store=True)
    company_id = fields.Many2one('res.company', string="Company", required=True, readonly=True, compute='_compute_project_manager')
    description = fields.Text(string="Description", tracking=True)
    stage_id = fields.Many2one('hr.request.overtime.stage', 'Stage', ondelete='restrict',
                            default=_get_default_stage_id, 
                            store=True, readonly=False,
                            group_expand='_read_group_stage_ids',
                            required=True, tracking=True,
                            # domain=lambda self: self._compute_domain_stage(),
                            copy=False, index=True,
                            )
    requester_id = fields.Many2one('res.users', string='Requester', readonly=False)

    user_id = fields.Many2one('res.users', string='Project Manager', tracking=True, readonly=True, compute='_compute_project_manager')
    active = fields.Boolean(string='Invisible Refuse Button', default=True)
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="All members has been assigned to the project", tracking=True)

    booking_overtime = fields.One2many('hr.booking.overtime', 'request_overtime_id', string='Booking Overtime')


    def archive_request_overtime(self):
        print('-------------------------------------')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """ Always display all stages """
        return stages.search([], order=order)

    @api.onchange('booking_overtime')
    def _add_booking_overtime(self):
        # update member_ids list
        user_ids = [
            user.user_id.id for user in self.booking_overtime.employee_id]
        self.member_ids = self.env['res.users'].search([('id', 'in', user_ids)])

    @api.onchange('project_id')
    def _compute_project_manager(self):
        for item in self:
            item.user_id = item.project_id.user_id or False
            item.company_id = item.project_id.company_id or False

    @api.model
    def create(self, vals_list):
        return super().create(vals_list)

        