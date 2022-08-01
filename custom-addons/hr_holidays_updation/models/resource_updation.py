from odoo import api, fields, models


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    company_id = fields.Many2one(
        'res.company', string="Company", readonly=True, store=True,
        default=lambda self: self.env.company, compute='_compute_company_id')

    @api.depends('calendar_id')
    def _compute_company_id(self):
        for leave in self:
            leave.company_id = self.env.company