from odoo import fields, models


class EventEvent(models.Model):
    """Event"""
    _inherit = 'event.event'
    _description = 'Event Update'

    organizer_id = fields.Many2one(
        'res.partner', string='Organizer', tracking=True,
        default=lambda self: self.env.company.partner_id,
        domain="[('email', '!=', False)]")

    address_id = fields.Many2one(
        'res.partner', string='Venue', default=lambda self: self.env.company.partner_id.id,
        tracking=True, domain="[('email', '!=', False)]")

class EventRegistration(models.Model):
    _inherit = 'event.registration'
    _description = 'Event Registration Update'

    partner_id = fields.Many2one(
        'res.partner', string='Booked by',
        states={'done': [('readonly', True)]},
        domain="[('email', '!=', False)]")