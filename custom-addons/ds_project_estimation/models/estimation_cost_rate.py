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
    cost_usd = fields.Monetary("Cost (USD)", currency_field="currency_usd_id")
    cost_yen = fields.Monetary("Cost (YEN)", currency_field="currency_yen_id", store=True, compute="compute_yen")
    cost_vnd = fields.Monetary("Cost (VND)", currency_field="currency_vnd_id", store=True, compute="compute_vnd")

    @api.depends('cost_usd')
    def compute_yen(self):
        exchange_rate_yen = self.env['estimation.exchange.rate'].search([('currency_id', '=', 24)])
        for rec in self:
            rec.cost_yen = rec.cost_usd * exchange_rate_yen.value

    @api.depends('cost_usd')
    def compute_vnd(self):
        exchange_rate_vnd = self.env['estimation.exchange.rate'].search([('currency_id', '=', 22)])
        for rec in self:
            rec.cost_vnd = rec.cost_usd * exchange_rate_vnd.value


class EstimationExchangeRate(models.Model):
    _name = "estimation.exchange.rate"
    _rec_name = "name"

    name = fields.Char(string="Name", store=True, compute="compute_name")
    usd_number = fields.Integer(string="USD", default=1, readonly=True, help="Number of USD")
    currency_id = fields.Many2one('estimation.currency',
                                  string="Currency",
                                  # domain="[('name', '!=', 'USD')]",
                                  help="Choosea Currency",
                                  required=True)
    value = fields.Float(string="Exchange Rate", required=True, digits=(12, 2))

    _sql_constraints = [
        ('unique_name', 'unique (currency_id)', 'Currency rates already exist!')
    ]

    @api.depends('currency_id')
    def compute_name(self):
        for record in self:
            if record.currency_id:
                record.name = "USD" + " --> " + record.currency_id.name


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