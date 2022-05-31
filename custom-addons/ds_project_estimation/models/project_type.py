from odoo import models, fields, api


class ProjectType(models.Model):
    """
    Project Type
    """
    _name ="project.type"
    _description = "Projet type estimation"
    _rec_name= "name"
    
    sequence = fields.Integer(string="No", readonly=True, index=True)
    name = fields.Char(string="Type name", required=True)
    description = fields.Char(string="Description")
    
    @api.model
    def create(self, vals):
        if vals:
            check = False
            for key in vals:
                if key == 'sequence':
                    check = True
            if check == False:
                ls_data = self.env['project.type'].search([])
                sequence_max = 0
                for record in ls_data:
                    if record.sequence > sequence_max:
                        sequence_max = record.sequence
                
                vals['sequence'] = sequence_max + 1
                return super(ProjectType, self).create(vals)
            else:
                return super(ProjectType, self).create(vals) 