from odoo import models, fields, api


class EstimationModuleAssumption(models.Model):
    _name = "estimation.module.assumption"
    _description = "Module Assumption of each estimation"

    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    assumption = fields.Text("Assumption")


class EstimationModuleSummary(models.Model):
    _name = "estimation.module.summary"
    _description = "Module Summary of each estimation"
    
    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    project_type = fields.Selection([("standard","Standard"), ("project","Project")], string="Project Type", required=True)
    time_effort_value = fields.Float(string="Value", required=True)

    working_efforts = fields.Selection([("hrs","Working hours per day"), ("days","Working days per month"),
                                        ("effort_day","Total efforts in man-day unit"), ("effort_mon","Total efforts in man-month unit")], 
                                        string="Working Time/Efforts", required=True)


class EstimationModuleEffort(models.Model):
    _name = "estimation.module.effort"
    _description = "Module Effort of each estimation"

    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    items = fields.Many2one('config.job_position', string="Item")
    effort = fields.Float(string="Effort")
    percent = fields.Char(string="Percentage")
