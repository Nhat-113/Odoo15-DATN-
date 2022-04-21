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
        vals_over = {'connect_overview': '', 'description': ''}
        if vals.get("number", "New") == "New":
            vals["number"] = self.env["ir.sequence"].next_by_code("estimation.work") or "New"
        result = super(Estimation, self).create(vals)
        est_current_id = self.env['estimation.work'].search([('number','=', vals["number"])])
        vals_over["connect_overview"] = est_current_id.id
        vals_over["description"] = 'Create New Estimation'
        self.env["estimation.overview"].create(vals_over)
        return result
    
    def write(self, vals):
        vals_over = {'connect_overview': self.id, 'description': ''}
        if vals:
            est_new_vals = vals.copy()
            ls_message_values = self.env['estimation.work'].search([('id','=',self.id)])
            est_old_vals = self.get_values(ls_message_values)
            est_desc_content = Estimation.merge_dict_vals(est_old_vals, est_new_vals)
            for key in est_desc_content:
                vals_over["description"] += key + ' : ' + est_desc_content[key]
                
            result = super(Estimation, self).write(vals)
            self.env["estimation.overview"].create(vals_over)
            return result    
        
    def convert_to_str(strings):
        for key in strings:
            if type(strings[key]) == int:
                strings[key] = str(strings[key])
        return strings
        
    def merge_dict_vals(a, b) :
        Estimation.convert_to_str(b)
        for keyb in b:
            for keya in a:
                if keyb == keya:
                    b[keyb] = ' --> '.join([a[keyb], b[keyb]])
                    break
        return b
        
    def get_values(self, est):
        vals_values = []
        mess_field = ["project_name",  "stage"] #"total_cost",
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids", "currency_id", "sale_order"] #, "message_main_attachment_id"
        mess_field_date = ["sale_date", "deadline"]
        for item in est:
            for i in mess_field:
                if item[i]:
                    vals_values.append(item[i])
                else:
                    vals_values.append('None')
            for j in mess_field_obj:
                if item[j].display_name:
                    vals_values.append(item[j].display_name)
                else:
                    vals_values.append('None')
            for k in mess_field_date:
                if item[k]:
                    temp = str(item[k].day) + '-' + str(item[k].month) + '-' + str(item[k].year)
                    vals_values.append(temp)
                else:
                    vals_values.append('None')
        
        vals_key = mess_field + mess_field_obj + mess_field_date
        value = dict(zip(vals_key, vals_values))
        return value

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