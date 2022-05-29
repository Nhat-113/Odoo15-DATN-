from odoo import models, fields, api

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
    currency_usd_id = fields.Many2one('res.currency', default= 2) # 2 is USD , string="Currency"
    currency_yen_id = fields.Many2one('res.currency', default= 25) # 2 is YEN , string="Currency"
    currency_vnd_id = fields.Many2one('res.currency', default= 23) # 2 is VND , string="Currency"
    cost_usd = fields.Monetary("Cost (USD)", currency_field="currency_usd_id")
    cost_yen = fields.Monetary("Cost (YEN)", currency_field="currency_yen_id", store=True, compute="compute_yen")
    cost_vnd = fields.Monetary("Cost (VND)", currency_field="currency_vnd_id", store=True, compute="compute_vnd")

    @api.depends('cost_usd')
    def compute_yen(self):
        exchange_rate_yen = self.env['estimation.exchange.rate'].search([('currency_id','=', self.currency_yen_id.id)])
        for rec in self:
            rec.cost_yen = rec.cost_usd * exchange_rate_yen.value
            
    @api.depends('cost_usd')
    def compute_vnd(self):
        exchange_rate_vnd = self.env['estimation.exchange.rate'].search([('currency_id','=', self.currency_vnd_id.id)])
        for rec in self:
            rec.cost_vnd = rec.cost_usd * exchange_rate_vnd.value

class EstimationExchangeRate(models.Model):
    _name="estimation.exchange.rate"
    _rec_name = "name"
    
    name = fields.Char(string="Name", store=True, compute="compute_name")
    usd_number = fields.Integer(string="USD", default= 1, readonly= True, help="Number of USD")
    currency_id = fields.Many2one('res.currency', 
                                  string="Currency", 
                                  domain="[('name', '!=', 'USD')]",
                                  help="Choosea Currency", 
                                  required=True)
    value = fields.Monetary(string="Exchange Rate", currency_field="currency_id", required=True, digits=(12,6))
    
    _sql_constraints = [
            ('unique_name', 'unique (currency_id)', 'Currency rates already exist!')
    ]
    
    @api.depends('currency_id')
    def compute_name(self):
        for record in self:
            if record.currency_id:
                record.name = "USD" + " --> " + record.currency_id.name
    