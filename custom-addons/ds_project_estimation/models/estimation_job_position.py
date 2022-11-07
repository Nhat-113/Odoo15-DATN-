from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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
    check_default = fields.Boolean("Is Default", default=False)

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
        if 'check_default' in vals:
            if vals['check_default'] == False:
                self.action_create_dynamic_fields(vals['job_position'])
        return super(JobPosition, self).create(vals)
           
           
    def action_create_dynamic_fields(self, field_label):
        field_name = 'x_' + field_label.casefold().replace(' ', '_') + '_effort'
        self.validate_character_job_position_input(field_name)
        self.create_dynamic_content('estimation.summary.totalcost', 'ds_project_estimation.estimation_totalcost_customize', field_name, field_label)
        self.create_dynamic_content('estimation.resource.effort', 'ds_project_estimation.estimation_resource_planning_customize_tree', field_name, field_label)

            
    def create_dynamic_content(self, model, views, field_name, field_label):
        model_dynamic_fields = self.env['ir.model'].search([('model', '=', model)])
        self.create_dynamic_field_content(field_name, field_label, model_dynamic_fields)
        self.create_dynamic_view_content(model, views, field_name, field_label)
        
        
    def create_dynamic_field_content(self, field_name, field_label, model_dynamic_fields):
        vals = {
                'name': field_name,
                'field_description': field_label,
                'model_id': model_dynamic_fields.id,
                'ttype': 'float',
                'readonly': True,
                'store': True
            }
        self.env['ir.model.fields'].sudo().create(vals)
        
    def create_dynamic_view_content(self, model, views, field_name, field_label):
        model_name = model.casefold().replace('.', '_')
        xml_inherit_id = self.env.ref(views)
        xml_arch = _('<?xml version="1.0" ?>'
                    '<data>'
                    '<field name="total_effort" position="before">'
                    '<field name="%s" sum="Total effort %s"/>'
                    '</field>'
                    '</data>') % (field_name, field_label)
        if model == 'estimation.resource.effort': 
            xml_arch = xml_arch.replace(_('sum="Total effort %s"') % (field_label), '')
        
        vals_xml = {
                    'name': 'dynamic_fields_customize_' + field_name + '_' + model_name,
                    'type': 'form',
                    'model': model,
                    'mode': 'extension',
                    'inherit_id': xml_inherit_id.id,
                    'arch_base': xml_arch,
                    'active': True
        }
        self.env['ir.ui.view'].sudo().create(vals_xml)
            
            
    def write(self, vals):
        if 'job_position' in vals and self.check_default == False:
            field_name_before = 'x_' + self.job_position.casefold().replace(' ', '_') + '_effort'
            field_name_after = 'x_' + vals['job_position'].casefold().replace(' ', '_') + '_effort'
            self.validate_character_job_position_input(field_name_after)
            get_fields = self.env['ir.model.fields'].sudo().search([('name', '=', field_name_before), 
                                                                    ('model', 'in', ['estimation.summary.totalcost', 'estimation.resource.effort'])])
            
            for field in get_fields:
                view_name = 'dynamic_fields_customize_' + field.name + '_' + field.model.casefold().replace('.', '_')
                xml_view_custome = self.env['ir.ui.view'].sudo().search([('name', '=', view_name), ('model', '=', field.model)])
                xml_arch_before = _('<field name="%s" sum="Total effort %s"/>') %(field.name, self.job_position)
                xml_arch_after = _('<field name="%s" sum="Total effort %s"/>') %(field_name_after, vals['job_position'])
                element_pseudo = '<header></header>'
                
                if field.model == 'estimation.resource.effort': 
                    xml_arch_before = xml_arch_before.replace(_(' sum="Total effort %s"') % (self.job_position), '')
                    xml_arch_after = xml_arch_after.replace(_(' sum="Total effort %s"') % (vals['job_position']), '')
                    
                #because we can't excute field change and view update at the same time!'
                #case 2: delete view old and update new field then create new view with new field -> issue: reset sequence field
                #case 1: using pesudo element for replace old fields then update view -> edit new field and re-update view
                if xml_view_custome:
                    xml_view_custome.sudo().write({
                        'arch': xml_view_custome.arch.replace(xml_arch_before, element_pseudo),
                        'arch_base': xml_view_custome.arch.replace(xml_arch_before, element_pseudo),
                        'arch_db': xml_view_custome.arch.replace(xml_arch_before, element_pseudo),
                    })
                    
                    field.sudo().write({'name': field_name_after, 'field_description': vals['job_position']})
                    
                    xml_view_custome.sudo().write({
                        'name': view_name.replace(field_name_before, field_name_after),
                        'arch': xml_view_custome.arch.replace(element_pseudo, xml_arch_after),
                        'arch_base': xml_view_custome.arch.replace(element_pseudo, xml_arch_after),
                        'arch_db': xml_view_custome.arch.replace(element_pseudo, xml_arch_after),
                    })
        
        return super(JobPosition, self).write(vals)
    
    
    def validate_character_job_position_input(self, job_position):
        try:
            models.check_pg_name(job_position)
        except ValidationError:
            msg = _("Job position names can only contain characters, digits and underscores (up to 63).")
            raise ValidationError(msg)
    
    def unlink(self):
        for record in self:
            if record.check_default == False:
                field_name = 'x_' + record.job_position.casefold().replace(' ', '_') + '_effort'
                
                get_fields = self.env['ir.model.fields'].sudo().search([('name', '=', field_name), 
                                                                    ('model', 'in', ['estimation.summary.totalcost', 'estimation.resource.effort'])])
                for field in get_fields:
                    view_name = 'dynamic_fields_customize_' + field.name + '_' + field.model.casefold().replace('.', '_')
                    xml_view_custome = self.env['ir.ui.view'].sudo().search([('name', '=', view_name), ('model', '=', field.model)])
                    if xml_view_custome:
                        xml_view_custome.sudo().unlink()
                    
                    field.sudo().unlink()
            else:
                raise ValidationError(_("You can't delete job position %s because it is required data !") % (record.job_position))
        return super(JobPosition, self).unlink()
                    