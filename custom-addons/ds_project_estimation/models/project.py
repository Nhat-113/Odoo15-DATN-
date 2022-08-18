from odoo import models, fields
import json

class Project(models.Model):
    """
    Project estimation inherit
    """
    _inherit = 'project.project'
    
    def _compute_estimation_id_domain(self):
        list_estimation = []
        project = self.env['project.project'].search([])
        for record in project:
            list_estimation.append(record.estimation_id.ids)

        flat_list = [item for sublist in list_estimation for item in sublist]
        
        self.estimation_id_domain = json.dumps(
                [('id', 'not in', flat_list)]
            )

    estimation_id_domain = fields.Char(compute="_compute_estimation_id_domain", readonly=True, store=False,)
    estimation_id = fields.Many2many('estimation.work', string="Estimation", domain="estimation_id_domain")
    
    