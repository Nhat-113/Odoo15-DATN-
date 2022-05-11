from odoo import models, fields, api, _


#hr.salary.rule
class Activities(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activities"
    _order = "sequence,id"
    _rec_name = "activity"

    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity_ids = fields.Many2one('estimation.work', string="Connect Module")
    activity_ids_break = fields.Many2one('estimation.work', string="Connect Module")

    activity = fields.Char("Activity")
    description = fields.Char("Description")
    effort = fields.Float(string="Effort", default=0, store=True, compute='_compute_total_effort')
    percent = fields.Float(string="Percentage", default=0)
    mandays = fields.Float(string="Expected (man-days)", default=0, store=True, compute='_compute_total_manday')
    parent_rule_id = fields.Many2one('config.activity', string='Parent Activity Rule', index=True)
    child_ids = fields.One2many('config.activity', 'parent_rule_id', string='Child Activity Rule', copy=True)
    activity_type = fields.Selection([('type_1', 'Type 1'),
                                      ('type_2', 'Type 2'),
                                      ('type_3', 'Type 3')],
                                    string='Activity type', 
                                    required=True,
                                    default='type_2',
                                    help='Please select activity type'
                                    )
    
    add_lines_breakdown_activity = fields.One2many('module.breakdown.activity', 'connect_module', string="Breakdown Activity")

    @api.depends('add_lines_breakdown_activity.effort')
    def _compute_total_effort(self):
        ls_break = self.env['module.breakdown.activity'].search([])
        for record in self:
            final_effort = 0.0
            for item in ls_break:
                if item.connect_module and (record.id == item.connect_module.id):
                    final_effort += item.effort
            record.effort = final_effort
            
    @api.depends('add_lines_breakdown_activity.mandays')
    def _compute_total_manday(self):
        ls_break = self.env['module.breakdown.activity'].search([])
        for record in self:
            final_manday = 0.0
            for item in ls_break:
                if item.connect_module and (record.id == item.connect_module.id):
                    final_manday += item.mandays
            record.mandays = final_manday
        
    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules

    @api.model
    def create(self, vals):
        if vals:
            check = False
            for key in vals:
                if key =='activity_ids_break':
                    check = True
                    break
            if check == True:
                result = super(Activities, self).create(vals)
                ctx = {
                    'sequence': vals['sequence'],
                    'activity': vals['activity'],
                    'effort': 0,
                    'percent': 0,
                    'estimation_id': vals['activity_ids_break'],
                    'activity_id': result['id']
                }
                self.env['module.effort.activity'].create(ctx)
                return result
            else:
                return super(Activities, self).create(vals)

    def unlink(self):
        for item in self:
            effort_distribute = self.env['module.effort.activity'].search([('activity_id','=', item.id)])
            breakdown_activity = self.env['module.breakdown.activity'].search([('connect_module','=', item.id)])
            if effort_distribute:
                effort_distribute.unlink()
            if breakdown_activity:
                breakdown_activity.unlink()
        return super(Activities, self).unlink()
        
#hr.payroll.structure
class ActivityStructure(models.Model):
    """
    Describe activity structure
    """
    _name = "config.activity.structure"
    _description = "Activity Structure"
    
    @api.model
    def _get_parent(self):
        return self.env.ref('ds_project_estimation.act_structure_base', False)
    
    name = fields.Char(string="Name")
    parent_id = fields.Many2one('config.activity.structure', string='Parent', default=_get_parent)
    children_ids = fields.One2many('config.activity.structure', 'parent_id', string='Children', copy=True)
    rule_ids = fields.Many2many('config.activity', 'config_structure_activity_rule_rel', 'struct_id', 'rule_id', string='Activity Rules')

    def get_all_rules(self):
        """
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """
        all_rules = []
        for struct in self:
            all_rules += struct.rule_ids._recursive_search_of_rules()
        return all_rules
    
    def _get_parent_structure(self):
        parent = self.mapped('parent_id')
        if parent:
            parent = parent._get_parent_structure()
        return parent + self


class DataActivity(models.Model):
    """
    Describe Data Activity
    """
    _name = "data.activity"
    _description = "Data Activity"
    _order = "sequence,id"

    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity")
    description = fields.Char("Description")


class DataActivityStructure(models.Model):
    """
    Describe Data Activity Structure
    """
    _name = "data.activity.structure"
    _description = "Data Activity Structure"

    @api.model
    def _get_parent(self):
        return self.env.ref('ds_project_estimation.act_structure_default_base', False)
    
    name = fields.Char(string="Name")
    rule_ids = fields.Many2many('data.activity', 'data_structure_activity_rule_rel', 'struct_id', 'rule_id', string='Activity Rules')
