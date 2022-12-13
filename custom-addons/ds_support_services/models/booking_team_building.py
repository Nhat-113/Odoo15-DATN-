import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class BookingTeamBuilding(models.Model):
    _name = "booking.team.building"

    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])
    currency_vnd = fields.Many2one('res.currency', string="VND Currency", default=lambda self: self._get_default_currency('VND'), readonly=True)  

    support_service_id = fields.Many2one('support.services', string='Support Service', readonly=False)
    employee_id = fields.Many2one(
        'hr.employee', string='Member', required=True, help="Member name assgin overtime")

    employee_id_domain = fields.Char(
        compute="_compute_employee_id_domain",
        readonly=True,
        store=False,
    )
    amount = fields.Monetary('Amount', default=200000, currency_field='currency_vnd')
    month = fields.Char('Month', compute="get_month_support_service", store=True)
    year = fields.Char('Year', compute="get_year_support_service", store=True)
    

    @api.depends('support_service_id.project_id')
    def _compute_employee_id_domain(self):
        for record in self:
            try:
                user_ids = record.support_service_id.project_id.planning_calendar_resources.employee_id.ids
            except:
                user_ids = []
            record.employee_id_domain = json.dumps(
                [('id', 'in', user_ids)]
            )

    @api.depends('support_service_id.get_month_tb')
    def get_month_support_service(self):
        for record in self:
            record.month = record.support_service_id.get_month_tb

    @api.depends('support_service_id.get_year_tb')
    def get_year_support_service(self):
        for record in self:
            record.year = record.support_service_id.get_year_tb

    @api.constrains('employee_id', 'amount', 'month', 'year')
    def check_validate_team_building(self):
        for record in self:
            booking_team_bds = self.env['booking.team.building'].search([
                ('employee_id', '=', record.employee_id.id), 
                ('month', '=', record.support_service_id.get_month_tb),
                ('year', '=', record.support_service_id.get_year_tb),
                ('id', '!=', record.id)
                ])
            if len(booking_team_bds)>0:
                raise UserError(_('There is another project requesting team building for %(employee)s in %(month)s/%(year)s.',
                employee=record.employee_id.name, month=record.support_service_id.get_month_tb, year=record.support_service_id.get_year_tb))