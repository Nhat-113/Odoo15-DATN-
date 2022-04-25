from odoo import models, fields, api


class EstimationResourcePlan(models.Model):
    _name = "estimation.resource.effort"
    _description = "Resource planning of each estimation"
    _order = "sequence,id"
    
    
    connect_resource_plan = fields.Many2one('estimation.work', string="Connect Resource Planning Effort")
    sequence = fields.Integer(string="No", )
    
    design_effort = fields.Float(string="Design",)
    dev_effort = fields.Float(string="Dev",)
    tester_effort = fields.Float(string="Tester",)
    comtor_effort = fields.Float(string="Comtor",)
    brse_effort = fields.Float(string="Brse",)
    pm_effort = fields.Float(string="PM",)
    
    total_effort = fields.Float(string="Total Effort (MD)")
    