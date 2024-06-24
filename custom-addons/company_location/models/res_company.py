from odoo import fields, models
from odoo.osv.expression import OR


class ResCompany(models.Model):
    _inherit = 'res.company'
    acceptance_distance = fields.Float("Acceptance Distance(meters)", default=300.0)