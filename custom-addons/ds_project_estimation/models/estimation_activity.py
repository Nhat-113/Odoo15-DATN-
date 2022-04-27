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
    effort = fields.Float(string="Effort", default=0,)
    percent = fields.Float(string="Percentage", default=0,)
    mandays = fields.Float(string="Expected (man-days)", default=0,)
    parent_rule_id = fields.Many2one('config.activity', string='Parent Activity Rule', index=True)
    child_ids = fields.One2many('config.activity', 'parent_rule_id', string='Child Activity Rule', copy=True)

    total_efforts = fields.Float(string="Total efforts", compute="_compute_total", store=True)
    total_mandays = fields.Float(string="Total man-days", compute="_compute_total", store=True)

    add_lines_breakdown_activity = fields.One2many('module.breakdown.activity', 'connect_module', string="Breakdown Activity")

    @api.depends('add_lines_breakdown_activity.effort', 'add_lines_breakdown_activity.mandays')
    def _compute_total(self):
        for line in self:
            pass
    

        
    def _recursive_search_of_rules(self):
        """
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in self.filtered(lambda rule: rule.child_ids):
            children_rules += rule.child_ids._recursive_search_of_rules()
        return [(rule.id, rule.sequence) for rule in self] + children_rules


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

