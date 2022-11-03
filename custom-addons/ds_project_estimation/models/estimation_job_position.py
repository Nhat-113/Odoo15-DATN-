from odoo import models, fields, api, _


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job.position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer(string="No", index=True)
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)

    _sql_constraints = [
            ('job_position_uniq', 'unique (job_position)', "Job position name already exists!"),
            ('sequence_uniq', 'unique (sequence)', "No already exists!")
        ]

    @api.model
    def create(self, vals):
        if 'sequence' in vals:
            ls_data = self.env['config.job.position'].search([])
            if ls_data:
                sequence_max = max(record.sequence for record in ls_data)
                vals['sequence'] = sequence_max + 1
                
        self.action_create_dynamic_fields(vals['job_position'])
        return super(JobPosition, self).create(vals)
           
           
    def action_create_dynamic_fields(self, field_label):
        field_name = 'x_' + field_label.casefold().replace(' ', '_') + '_effort'
        model_dynamic_fields = self.env['ir.model'].search([('model', 'in', ['estimation.summary.totalcost'])]) #, 'estimation.resource.effort'
        for model in model_dynamic_fields:
            vals = {
                'name': field_name,
                'field_description': field_label,
                'model_id': model.id,
                'ttype': 'float',
                'readonly': True,
                'store': True
            }
            self.env['ir.model.fields'].sudo().create(vals)
            xml_inherit_id = self.env.ref('ds_project_estimation.estimation_totalcost_customize')
            xml_arch = _('<?xml version="1.0" ?>'
                        '<data>'
                        '<field name="%s" position="%s">'
                        '<field name="%s" sum="Total effort %s"/>'
                        '</field>'
                        '</data>') % ('pm_effort', 'after', field_name, field_label)
            
            vals_xml = {
                        'name': 'dynamic_fields_customize_' + field_name,
                        'type': 'form',
                        'model': 'estimation.summary.totalcost',
                        'mode': 'extension',
                        'inherit_id': xml_inherit_id.id,
                        'arch_base': xml_arch,
                        'active': True
            }
            
            self.env['ir.ui.view'].sudo().create(vals_xml)
            
            