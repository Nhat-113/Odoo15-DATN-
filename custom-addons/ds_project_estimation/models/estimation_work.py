# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Estimation(models.Model):
    """
    Describes a work estimation.
    """
    _name = "estimation.work"
    _description = "Estimation"
    _rec_name = "number"

    project_name = fields.Char("Project Name", required=True)
    number = fields.Char("No", readonly=True, required=True, copy=False, index=False, default="New")

    estimator_ids = fields.Many2one('res.users', string='Estimator', default=lambda self: self.env.user, readonly=True)
    reviewer_ids = fields.Many2one('res.users', string='Reviewer', default=lambda self: self.env.user)
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency")

    expected_revenue = fields.Float(string="Expected Revenue")
    total_cost = fields.Float(string="Total Cost")

    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    stage = fields.Selection([("new","New"), ("in_progress","In Progress"), ("pending","Pending")], string="Status", required=True)
    
    contract_id = fields.Many2one('hr.contract', string='Contract', help="Contract")
    # struct_id = fields.Many2one('config.activity.structure', string='Structure', readonly=True)

    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_module_assumption = fields.One2many('estimation.module.assumption', 'connect_module', string='Module Assumption')
    add_lines_module_summary = fields.One2many('estimation.module.summary', 'connect_module', string='Module Summary')
    
    # def _get_default_activities(self):
    #     return self.env['config.activity'].search([])
    add_lines_module_effort = fields.One2many('config.activity', 'activity_ids', string='Module Effort')
    
    
    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'connect_summary', string='Summary Total Cost')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'connect_summary_costrate', string='Summary Cost Rate')

    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'connect_resource_plan', string='Resource Planning Effort')
    
    
    @api.model
    def create(self, vals):
        vals_over = {'connect_overview': '', 'description': ''}
        if vals.get("number", "New") == "New":
            vals["number"] = self.env["ir.sequence"].next_by_code("estimation.work") or "New"
        result = super(Estimation, self).create(vals)
        est_current_id = self.env['estimation.work'].search([('number','=', vals["number"])])
        vals_over["connect_overview"] = est_current_id.id
        vals_over["description"] = 'Create New Estimation'
        self.env["estimation.overview"].create(vals_over)
        return result

    @api.model
    def get_inputs(self, contracts):
        res = []
        structure_ids = contracts.get_all_structures()
        
        rule_ids = self.env['config.activity.structure'].browse(structure_ids).get_all_rules()
        
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['config.activity'].browse(sorted_rule_ids)
        
        for contract in contracts:
            for input in inputs:
                input_data = {
                    'sequence': input.sequence,
                    'activity': input.activity,
                    'effort': input.effort,
                    'percent': input.percent
                }
                res += [input_data]
        
        return res

    @api.onchange('')
    def onchange_module_effort(self):
        # if not self.contract_id.struct_id:
        #     return

        # if self.contract_id:
        contract_ids = self.contract_id.ids
        contracts = self.env['hr.contract'].browse(contract_ids)

        effort_lines = self.get_inputs(contracts)
        input_lines = self.add_lines_module_effort.browse([])
        for r in effort_lines:
            input_lines += input_lines.new(r)
        self.add_lines_module_effort = input_lines
        return

    @api.onchange('contract_id')
    def onchange_contract(self):
        # if not self.contract_id:
        #     self.struct_id = False
        self.with_context(contract=True).onchange_module_effort()
        return
    
    def write(self, vals):
        vals_over = {'connect_overview': self.id, 'description': ''}
        if vals:
            est_new_vals = vals.copy()
            ls_message_values = self.env['estimation.work'].search([('id','=',self.id)])
            est_old_vals = self.get_values(ls_message_values)
            est_desc_content = self.merge_dict_vals(est_old_vals, est_new_vals)
            est_desc_content_convert = est_desc_content.copy()
            self.convert_field_to_field_desc(est_desc_content_convert)
            for key in est_desc_content_convert:
                vals_over["description"] += key + ' : ' + est_desc_content_convert[key]
            
            result = super(Estimation, self).write(vals)
            self.env["estimation.overview"].create(vals_over)
            return result 

    def convert_field_to_field_desc(self, dic):
        result = dic.copy()
        field = self.env['ir.model.fields']
        for item in result:
            if field.search([('name','=',item),('model','=','estimation.work')]):
                dic[field.search([('name','=',item),('model','=','estimation.work')]).field_description] = dic.pop(item)
        return dic
    
    def convert_to_str(strings):
        for key in strings:
            if type(strings[key]) == int:
                strings[key] = str(strings[key])
        return strings
      
    def convert_id_to_name_desc(self, vals):
        # "estimator_ids" because "estimator_ids" can't update (readonly) -> unnecessary
        # ls_keys = ["reviewer_ids", "customer_ids", "currency_id", "sale_order"]   because only fields  in vals have id
        for item in vals:
            if item == "reviewer_ids":
                vals[item] = self.env['res.users'].search([('id','=',vals[item])]).name
            elif item == "customer_ids":
                vals[item] = self.env['res.partner'].search([('id','=',vals[item])]).name
            elif item == "currency_id":
                vals[item] = self.env['res.currency'].search([('id','=',vals[item])]).name
            # elif item == "sale_order":
            #     vals[item] = self.env['sale.order'].search([('id','=',vals[item])]).name
        return vals
        
    def merge_dict_vals(self, a, b) :
        Estimation.convert_to_str(b)
        self.convert_id_to_name_desc(b)
        for keyb in b:
            for keya in a:
                if keyb == keya:
                    b[keyb] = ' --> '.join([a[keyb], b[keyb]]) + '\n'
                    break
        return b
        
    def get_values(self, est):
        vals_values = []
        mess_field = ["project_name",  "stage"] #"total_cost",
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids", "currency_id",] #, "message_main_attachment_id"
        mess_field_date = ["sale_date", "deadline"]
        for item in est:
            for i in mess_field:
                if item[i]:
                    vals_values.append(item[i])
                else:
                    vals_values.append('None')
            for j in mess_field_obj:
                if item[j].display_name:
                    vals_values.append(item[j].display_name)
                else:
                    vals_values.append('None')
            for k in mess_field_date:
                if item[k]:
                    temp = str(item[k].day) + '-' + str(item[k].month) + '-' + str(item[k].year)
                    vals_values.append(temp)
                else:
                    vals_values.append('None')
        
        vals_key = mess_field + mess_field_obj + mess_field_date
        value = dict(zip(vals_key, vals_values))
        return value


class CostRate(models.Model):
    """
    Describe cost rate.
    """
    _name = "cost.rate"
    _description = "CostRate"
    _order = "sequence,id"
    _rec_name = "sequence"

    sequence = fields.Integer()
    role = fields.Char("Role", required=True)
    description = fields.Char("Description", required=True)
    cost_usd = fields.Float("Cost (USD)")
    cost_yen = fields.Float("Cost (YEN)", compute="_compute_yen")
    cost_vnd = fields.Float("Cost (VND)", compute="_compute_vnd")

    def _compute_yen(self):
        for rec in self:
            rec.cost_yen = rec.cost_usd * data['JPY']

    def _compute_vnd(self):
        for rec in self:
            rec.cost_vnd = rec.cost_usd * 22859.50


class JobPosition(models.Model):
    """
    Describe job position in configuration.
    """
    _name = "config.job_position"
    _description = "Job Position"
    _order = "sequence,id"
    _rec_name = "job_position"

    sequence = fields.Integer()
    job_position = fields.Char("Job Position", required=True)
    description = fields.Char("Description", required=True)
    effort = fields.Float(string="Effort", default=0.0)
    percent = fields.Char(string="Percentage", default="0.0")


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
    job_pos = fields.Many2one('config.job_position', string="Job Position")
    activity = fields.Char("Activity")
    description = fields.Char("Description", )
    effort = fields.Float(string="Effort", default=0)
    percent = fields.Char(string="Percentage", default="0.0")
    parent_rule_id = fields.Many2one('config.activity', string='Parent Activity Rule', index=True)
    child_ids = fields.One2many('config.activity', 'parent_rule_id', string='Child Activity Rule', copy=True)

    @api.constrains('parent_rule_id')
    def _check_parent_rule_id(self):
        if not self._check_recursion(parent='parent_rule_id'):
            raise ValidationError(_('Error! You cannot create recursive hierarchy of Activity Rules.'))

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
    
    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create a recursive salary structure.'))
    
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
    
