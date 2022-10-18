from email.policy import default
from odoo import models, fields, api, tools
import math


class CostRate(models.Model):
    """
    Describe cost rate.
    """
    _name = "cost.rate"
    _description = "CostRate"
    _order = "id"
    _rec_name = "role"

    role = fields.Char("Role", required=True)
    description = fields.Char("Description", required=True)
    job_type = fields.Many2one('config.job.position', string='Type')
    currency_usd_id = fields.Many2one('estimation.currency', default=1)  # 2 is USD , string="Currency"
    currency_yen_id = fields.Many2one('estimation.currency', default=24)  # 2 is YEN , string="Currency"
    currency_vnd_id = fields.Many2one('estimation.currency', default=22)  # 2 is VND , string="Currency"
    currency_sgd_id = fields.Many2one('estimation.currency', default=36)
    cost_usd = fields.Float("Cost (USD)", )
    cost_yen = fields.Float("Cost (JPY)", store=True,)
    cost_vnd = fields.Float("Cost (VND)", store=True,)
    cost_sgd = fields.Float("Cost (SGD)", store=True)

class EstimationExchangeRate(models.Model):
    _name = "estimation.currency"
    _description = "Estimation Currency"

    name = fields.Char(string='Currency', size=3, required=True, help="Currency Code (ISO 4217)")
    full_name = fields.Char(string='Name')
    symbol = fields.Char(help="Currency sign, to be used when printing amounts.", required=True)
    rounding = fields.Float(string='Rounding Factor', digits=(12, 6), default=0.01, )
    decimal_places = fields.Integer(compute='_compute_decimal_places', store=True, )

    def round(self, amount):
        """Return ``amount`` rounded  according to ``self``'s rounding rules.

           :param float amount: the amount to round
           :return: rounded float
        """
        self.ensure_one()
        return tools.float_round(amount, precision_rounding=self.rounding)

    @api.depends('rounding')
    def _compute_decimal_places(self):
        for currency in self:
            if 0 < currency.rounding < 1:
                currency.decimal_places = int(math.ceil(math.log10(1 / currency.rounding)))
            else:
                currency.decimal_places = 0