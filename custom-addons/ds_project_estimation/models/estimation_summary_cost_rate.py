from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class EstimationSummaryCostRate(models.Model):
    _name = "estimation.summary.costrate"
    _description = "Summary of cost rate in each estimation"
    _order = "sequence"
    _rec_name = "name"

    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    total_cost_id = fields.Many2one('estimation.summary.totalcost', string="Total Cost")
    name = fields.Char(string="Components", store=True)
    key_primary = fields.Char(string="Key unique module")

    sequence = fields.Integer(string="No", store=True)
    job_position = fields.Many2one('config.job.position', string="Type", store=True)
    role = fields.Many2one('cost.rate', string='Role', store=True)
    yen_day = fields.Float(string="Unit (Currency/Day)", store=True, compute='_compute_yen_day')
    yen_month = fields.Float(string="Unit (Currency/Month)", store=True)
    
    is_lock = fields.Boolean(string="Is Lock", default=False)
    
    
    @api.depends('yen_month')
    def _compute_yen_day(self):
        for record in self:
            record.yen_day = record.yen_month / 20
            
            
    @api.constrains('yen_month')
    def validate_lock_cost_rate(self):
        for record in self:
            if record.is_lock == True:
                raise ValidationError(_("This module has been generated successfully, so you cannot modify the content of this module!"))
