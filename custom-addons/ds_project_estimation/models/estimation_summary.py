from odoo import models, fields, api


class EstimationSummaryTotalCost(models.Model):
    _name = "estimation.summary.totalcost"
    _description = "Summary of each estimation"
    _order = "sequence,id"
    
    connect_summary = fields.Many2one('estimation.work', string="Connect Summary")
    
    sequence = fields.Integer(string="No", )
    module = fields.Char(string="Components",)
    design_effort = fields.Float(string="Design",)
    dev_effort = fields.Float(string="Dev",)
    tester_effort = fields.Float(string="Tester",)
    comtor_effort = fields.Float(string="Comtor",)
    brse_effort = fields.Float(string="Brse",)
    pm_effort = fields.Float(string="PM",)
    
    total_effort = fields.Float(string="Total Effort (MD)")
    cost = fields.Float(string="Cost (YEN)")


class EstimationSummaryCostRate(models.Model):
    _name = "estimation.summary.costrate"
    _description = "Summary of cost rate in each estimation"
    _order = "sequence,id"
    
    connect_summary_costrate = fields.Many2one('estimation.work', string="Connect Summary Cost Rate")
    
    sequence = fields.Integer(string="No", )
    types = fields.Char(string="Type", )
    yen_month = fields.Float(string="Unit (YEN/Month)",)
    yen_day = fields.Float(string="Unit (YEN/Day)",)
    vnd_day = fields.Float(string="Unit (VND/Day)",)
