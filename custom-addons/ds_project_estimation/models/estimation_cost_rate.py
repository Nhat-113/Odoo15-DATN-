from odoo import models, fields, api
from forex_python.converter import CurrencyRates

c = CurrencyRates()
data = c.get_rates('USD')


class CostRate(models.Model):
    """
    Describe cost rate.
    """
    _name = "cost.rate"
    _description = "CostRate"
    _order = "sequence,id"
    _rec_name = "sequence"

    sequence = fields.Integer()
    role = fields.Char("Role", required=True)
    description = fields.Char("Description", required=True)
    cost_usd = fields.Float("Cost (USD)")
    cost_yen = fields.Float("Cost (YEN)", compute="_compute_yen")
    cost_vnd = fields.Float("Cost (VND)", compute="_compute_vnd")

    def _compute_yen(self):
        for rec in self:
            rec.cost_yen = rec.cost_usd * data['JPY']

    def _compute_vnd(self):
        for rec in self:
            rec.cost_vnd = rec.cost_usd * 22859.50
