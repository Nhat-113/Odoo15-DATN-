from odoo import api, fields, models, _
import json
import requests
from datetime import datetime
from odoo.exceptions import ValidationError

class GetAPIDataExchangeRate(models.Model):
    _name = "api.exchange.rate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Exchange rate"
    _rec_name = "name"
    
    def _get_default_currency(self, type_currency):
        return self.env['res.currency'].search([('name', '=', type_currency)])

    def _get_default_name_exchange_rate(self):
        return "Exchange Rate"

    name = fields.Char(string="Exchange Rate", default="Exchange Rate")
    usd_convert = fields.Monetary(string="USD to VND", currency_field='currency_id')
    jpy_convert = fields.Monetary(string="JPY to VND", currency_field='currency_id')
    date_upgrade = fields.Datetime(string="Date upgrade")
    count_upgrade = fields.Integer(string="Number of Upgrades", readonly=True, tracking=True)
    message_warning = fields.Char(string="Warning", 
                                  default="The number of exchange rate updates for the day has expired! Please update tomorrow")
    maximum_upgrade = fields.Integer(string="Maximum Upgrades", default=8, tracking=True)
    
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, readonly=True, default=lambda self: self._get_default_currency('VND'))
    
    
    def upgrade_exchane_rate_api(self):
        if self.count_upgrade == self.maximum_upgrade:
            raise ValidationError(_("The number of exchange rate updates for the day has expired! Please update tomorrow"))
        else:
            self.count_upgrade += 1
            self.update({
                "usd_convert": self.get_currency_api("USD"),
                "jpy_convert": self.get_currency_api("JPY"),
                "date_upgrade": datetime.now()
            })
        
    def get_currency_api(self, currency):
        data = {}
        api_url = "https://open.er-api.com/v6/latest/" + currency
        response = requests.get(api_url, data=json.dumps(data))
        res = response.json()
        return res["rates"]["VND"]
    
    
    def write(self, vals):
        if 'date_upgrade' not in vals:
            vals['date_upgrade'] = datetime.now()
        result = super(GetAPIDataExchangeRate, self).write(vals)
        return result