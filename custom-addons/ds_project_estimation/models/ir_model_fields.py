from odoo import models, fields, api


class DynamicFields(models.Model):
    _name = 'dynamic.fields'
    _description = 'Dynamic Field Creation'
    _inherit = 'ir.model.fields'
    
    
    # def get_possible_field_types(self):
    #     field_lists = sorted((key, key) for key in fields.MetaField.by_type)
    #     field_lists.remove(('one2many', 'one2many'))
    #     field_lists.remove(('many2many', 'many2many'))
    #     field_lists.remove(('reference', 'reference'))
    #     return field_lists
    
    
    position_field = fields.Many2one('ir.model.fields', string='Field Name')
    position = fields.Selection([('before', 'Before'), ('after', 'After')], string='Position', required=True)
    groups = fields.Many2many('res.groups', 'dynamic_field_creation_id', 'field_id', 'group_id')
    # model_id = fields.Many2one('ir.model', string='Model', required=True, index=True, ondelete='cascade')
    # ref_model_id = fields.Many2one('ir.model', string='Model', index=True)
    # field_type = fields.Selection(selection='get_possible_field_types', string='Field Type', required=True)
    
    
class Groups(models.Model):
    _inherit = 'res.groups'
    
    
    dynamic_field_creation_id = fields.Many2one('dynamic.fields')