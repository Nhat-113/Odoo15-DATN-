from odoo import models, fields, api


class ProjectType(models.Model):
    """
    Project Type
    """
    _name ="project.type"
    _description = "Projet type estimation"
    _rec_name= "name"
    
    sequence = fields.Integer(string="No", index=True)
    name = fields.Char(string="Type name", required=True)
    description = fields.Char(string="Description")
    
    _sql_constraints = [
            ('name_uniq', 'unique (name)', "Project type name already exists!"),
            ('sequence_uniq', 'unique (sequence)', "No already exists!")
        ]
    
    @api.model
    def create(self, vals):
        if 'sequence' in vals:
            ls_data = self.env['project.type'].search([])
            if ls_data:
                sequence_max = max(record.sequence for record in ls_data)
                vals['sequence'] = sequence_max + 1
        return super(ProjectType, self).create(vals)