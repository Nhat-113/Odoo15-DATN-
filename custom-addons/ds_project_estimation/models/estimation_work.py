# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Estimation(models.Model):
    """
    Describes a work estimation.
    """
    _name = "estimation.work"
    _description = "Estimation"
    _rec_name = "number"


    project_name = fields.Char("Project Name", required=True)
    number = fields.Char("No", readonly=True, required=True, copy=False, index=False, default="New")

    estimator_ids = fields.Many2one('res.users', string='Estimator', default=lambda self: self.env.user, readonly=True)
    reviewer_ids = fields.Many2one('res.users', string='Reviewer', default=lambda self: self.env.user)
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True)

    # company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.user.company_id.id, index=1)
    currency_id = fields.Many2one("res.currency", string="Currency")
    sale_order = fields.Many2one('sale.order', string="Sale Order")
    expected_revenue = fields.Monetary("Expected Revenue", related="sale_order.amount_total")

    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    stage = fields.Selection([("new","New"), ("in_progress","In Progress"), ("pending","Pending")], string="Stage", required=True)
    
    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_module_assumption = fields.One2many('estimation.module.assumption', 'connect_module', string='Module Assumption')
    add_lines_module_summary = fields.One2many('estimation.module.summary', 'connect_module', string='Module Summary')
    add_lines_module_effort = fields.One2many('estimation.module.effort', 'connect_module', string='Module Effort')
    


    @api.model
    def create(self, vals):
        if vals.get("number", "New") == "New":
            vals["number"] = self.env["ir.sequence"].next_by_code("estimation.work") or "New"
        result = super(Estimation, self).create(vals)
        return result


class EstimationOverview(models.Model):
    _name = "estimation.overview"
    _description = "Overview of each estimation"

    connect_overview = fields.Many2one('estimation.work', string="Connect Overview")
    
    # Notebook and pages
    author = fields.Many2one('res.users', string="Author", default=lambda self: self.env.user, readonly=True)
    revision = fields.Char("Revision", readonly=True, copy=False, index=False, default="/")
    description = fields.Text("Description", default="Nothing")

    @api.model
    def create(self, vals):
        if vals.get("revision", "/") == "/":
            vals["revision"] = self.env["ir.sequence"].next_by_code("estimation.overview") or "/"
        result = super(EstimationOverview, self).create(vals)
        return result


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
    items = fields.Many2one('config.activity', string="Item")
    



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
    cost = fields.Float("Cost (USD)")


class Activity(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activity"
    _order = "sequence,id"
    _rec_name = "activities"

    sequence = fields.Integer()
    activities = fields.Char("Activities", required=True)
    description = fields.Char("Description", required=True)
