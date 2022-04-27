from odoo import models, fields, api


class EstimationModuleAssumption(models.Model):
    _name = "estimation.module.assumption"
    _description = "Module Assumption of each estimation"

    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    assumption = fields.Text("Assumption")


class EstimationModuleSummary(models.Model):
    _name = "estimation.module.summary"
    _description = "Module Summary of each estimation"
    
    name = fields.Char(string="Name")
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    project_type = fields.Char(string="Project Type")
    time_effort_value = fields.Float(string="Value",)

    working_efforts = fields.Char(string="Working Time/Efforts")

    # parent_rule_id = fields.Many2one('estimation.module.summary', string='Parent Summary Rule', index=True)
    # child_ids = fields.One2many('estimation.module.summary', 'parent_rule_id', string='Child Summary Rule', copy=True)

    # def _recursive_search_of_rules(self):
    #     """
    #     @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
    #     """
    #     children_rules = []
    #     for rule in self.filtered(lambda rule: rule.child_ids):
    #         children_rules += rule.child_ids._recursive_search_of_rules()
    #     return [(rule.id, rule.sequence) for rule in self] + children_rules


# class EstimationModuleSummaryStructure(models.Model):
#     """
#     Summary Structure in Module
#     """
#     _name = "module.summary.structure"
#     _description = "Summary Module Structure"

#     @api.model
#     def _get_parent(self):
#         return self.env.ref('ds_project_estimation.module_summary_base', False)

#     name = fields.Char(string="Name")
#     parent_id = fields.Many2one('module.summary.structure', string='Parent', default=_get_parent)
#     children_ids = fields.One2many('module.summary.structure', 'parent_id', string='Children', copy=True)
#     rule_ids = fields.Many2many('estimation.module.summary', 'module_summary_rule_rel', 'struct_id', 'rule_id', string='Summary Rules')

#     def get_all_rules(self):
#         """
#         @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
#         """
#         all_rules = []
#         for struct in self:
#             all_rules += struct.rule_ids._recursive_search_of_rules()
#         return all_rules

#     def _get_parent_structure(self):
#         parent = self.mapped('parent_id')
#         if parent:
#             parent = parent._get_parent_structure()
#         return parent + self


class BreakdownActivities(models.Model):
    """
    Describe breakdown activities
    """
    _name = "module.breakdown.activity"
    _description = "Module Breakdown of each activity"
    _order = "sequence,id"

    connect_module = fields.Many2one('config.activity', string="Connect Module")
    
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity")
    job_pos = fields.Many2one('config.job_position', string="Job Position")
    effort = fields.Float(string="Effort", default=0)
    mandays = fields.Float(string="Expected (man-days)", default=0)

    @api.depends('effort', 'mandays')
    def _compute_all(self):
        pass
    
    