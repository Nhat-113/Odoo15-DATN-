from odoo import api, fields, models, _

class ProjectExpense(models.Model):
    _inherit = 'project.expense.value'
    
    def _get_default_project_management_id(self):
        return self.env['project.management'].search([('project_id', '=', self.project_id.id)]).id
        
    project_management_id = fields.Many2one('project.management', string="Project Management", 
                                            default=_get_default_project_management_id, 
                                            compute='_get_default_project_management', 
                                            store=True)
    
    @api.depends('project_id')
    def _get_default_project_management(self):
        for record in self:
            get_project_management_id = self.env['project.management'].search([('project_id', '=', record.project_id.id)]).id
            record.project_management_id = get_project_management_id