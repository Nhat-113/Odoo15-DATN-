from odoo import models, fields, api

class Project(models.Model):
    """
    Project estimation inherit
    """
    _inherit = 'project.project'
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation", groups="ds_project_estimation.estimation_access_sale")
    department_id = fields.Many2one("hr.department", string="Department", domain="[('company_id','=', company_id)]", groups="ds_project_estimation.estimation_access_sale")

    total_mm = fields.Float(string="Total Effort Estimate (Man Month)", store=True, compute="_compute_total_mm", groups="ds_project_estimation.estimation_access_sale")

    @api.depends("estimation_id")
    def _compute_total_mm(self):
        for record in self:
            for item in record.estimation_id.add_lines_resource_effort:
                if item.key_primary == 'Total (MM)':
                    record.total_mm = item.total_effort
        