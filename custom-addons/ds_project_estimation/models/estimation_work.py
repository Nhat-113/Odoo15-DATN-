# -*- coding: utf-8 -*-

from odoo import models, fields, api
from forex_python.converter import CurrencyRates

c = CurrencyRates()
data = c.get_rates('USD')


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
    total_cost = fields.Monetary(string="Total Cost")

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


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job_position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer()
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)
    effort = fields.Float(string="Effort", default=0.0)
    percent = fields.Char(string="Percentage", default="0.0")


class Activities(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activities"
    _order = "sequence,id"
    _rec_name = "activity"

    sequence = fields.Integer(required=True, index=True, default=5, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity", required=True)
    description = fields.Char("Description", required=True)