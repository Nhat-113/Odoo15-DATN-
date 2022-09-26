from odoo import models, fields, api

class Project(models.Model):
    """
    Project estimation inherit
    """
    _inherit = 'project.project'
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation", groups="ds_project_estimation.estimation_access_sale")
    department_id = fields.Many2one("hr.department", string="Department", domain="[('company_id','=', company_id)]", groups="ds_project_estimation.estimation_access_sale")

    total_mm = fields.Float(string="Total Effort Estimate (Man Month)", compute="_compute_total_mm", groups="ds_project_estimation.estimation_access_sale")

    @api.depends("estimation_id")
    def _compute_total_mm(self):
        estimation_resource_effort = self.env['estimation.resource.effort'].search([('estimation_id','=',self.estimation_id.id),('name','=','Total (MM)')])
        if estimation_resource_effort:
            self.total_mm = estimation_resource_effort.total_effort
        else:
            self.total_mm = 0