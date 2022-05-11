# -*- coding: utf-8 -*-

from email.policy import default
from odoo import models, fields, api, _


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
    
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays")

    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    stage = fields.Selection([("new","New"), ("in_progress","In Progress"), ("pending","Pending")], string="Status", required=True)

    contract_id = fields.Many2one('hr.contract', string='Contract', help="Contract")
    # struct_id = fields.Many2one('config.activity.structure', string='Structure', readonly=True)

    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')

    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'connect_summary', string='Summary Total Cost')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'connect_summary_costrate', string='Summary Cost Rate')
    
    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'connect_resource_plan', string='Resource Planning Effort')

    add_lines_module_assumption = fields.One2many('estimation.module.assumption', 'connect_module', string='Module Assumption')
    add_lines_module_summary = fields.One2many('estimation.module.summary', 'connect_module', string='Module Summary')
    
    # def _get_default_activities(self):
    #     return self.env['config.activity'].search([])

    add_lines_module_effort = fields.One2many('config.activity', 'activity_ids', string='Module Effort')
    add_lines_module_breakdown = fields.One2many('config.activity', 'activity_ids_break', string="Breakdown Structure")
    add_lines_module_effort_distribute = fields.One2many('module.effort.activity', 'estimation_id', string='Module Effort')

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

    @api.onchange('reviewer_ids')
    def onchange_module_effort(self):
        # if not self.contract_id.struct_id:
        #     return

        # if self.contract_id:
        contract_ids = self.contract_id.ids
        contracts = self.env['hr.contract'].browse(contract_ids)

        effort_lines = self.get_inputs(contracts)
        input_lines = self.add_lines_module_effort.browse([])
        input_lines_breakdown = self.add_lines_module_breakdown.browse([])
        # input_lines_sum = self.add_lines_module_summary.browse([])
        for r in effort_lines:
            input_lines += input_lines.new(r)
            input_lines_breakdown += input_lines_breakdown.new(r)
    
        self.add_lines_module_breakdown = input_lines_breakdown
        self.add_lines_module_effort = input_lines
        return

    @api.onchange('contract_id')
    def onchange_contract(self):
        # if not self.contract_id:
        #     self.struct_id = False
        self.with_context(contract=True).onchange_module_effort()
        return
    
    @api.depends('add_lines_module_breakdown.mandays')
    def _compute_total_mandays(self):
        ls_activity = self.env['config.activity'].search([('activity_ids_break', '=', self.id)])
        total = 0.0
        for item in ls_activity:
            total += item.mandays
        for record in self:
            record.total_manday = total
    
    def write(self, vals):
        vals_over = {'connect_overview': self.id, 'description': ''}
        if vals:
            est_new_vals = vals.copy()
            ls_message_values = self.env['estimation.work'].search([('id','=',self.id)])
            est_old_vals = self.get_values(ls_message_values)
            vals_tab_module = self.convert_new_dict(est_new_vals)
            est_desc_content = self.merge_dict_vals(est_old_vals, est_new_vals, vals_tab_module)
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
            elif type(strings[key]) == bool:
                strings[key] = ''
        return strings
      
    def convert_id_to_name_desc(self, vals):
        # "estimator_ids" because "estimator_ids" can't update (readonly) -> unnecessary
        # ls_keys = ["reviewer_ids", "customer_ids", "currency_id", "sale_order"]   because only fields  in vals have id
        for item in vals:
            if item == "reviewer_ids" and vals[item] != '':
                vals[item] = self.env['res.users'].search([('id','=',vals[item])]).name
            elif item == "customer_ids" and vals[item] != '':
                vals[item] = self.env['res.partner'].search([('id','=',vals[item])]).name
            elif item == "currency_id" and vals[item] != '':
                vals[item] = self.env['res.currency'].search([('id','=',vals[item])]).name
            # elif item == "sale_order" and vals[item] != '':
            #     vals[item] = self.env['sale.order'].search([('id','=',vals[item])]).name
            elif item == "contract_id" and vals[item] != '':
                vals[item] = self.env['hr.contract'].search([('id','=',vals[item])]).name
        return vals
        
    def merge_dict_vals(self, a, b, vals_tab_module) :
        Estimation.convert_to_str(b)
        self.convert_id_to_name_desc(b)
        for keyb in b:
            for keya in a:
                if keyb == keya:
                    if b[keyb] == '':
                        b[keyb] = ' --> '.join([a[keyb], 'None'])
                    else:
                        b[keyb] = ' --> '.join([a[keyb], b[keyb]])
                    break
        
        Estimation.ouput_message(b, vals_tab_module);
        return b
    
    def ouput_message(b, vals_tab_module):
        mess_tab_list = {'add_lines_summary_totalcost': 'Total Cost',
                         'add_lines_summary_costrate': 'Cost Rate',
                         'add_lines_resource_effort': 'Total Effort', 
                         'add_lines_module_assumption': 'Assumption', 
                         'add_lines_module_summary': 'Summary', 
                         'add_lines_module_effort': 'Effort Distribution',
                         'add_lines_module_breakdown': 'Work Breakdown Structure and Estimate'}
        key_output = {'add_lines_summary': 'Summary', 'add_lines_resource': 'Resource Planning', 'add_lines_module': 'Module'}
        for key in vals_tab_module:
            for tab in mess_tab_list:
                if key == tab:
                    for op in key_output:
                        if tab.find(op) != -1:
                            bkey = key_output[op]
                            if Estimation.find_key_in_dict (b, bkey):
                                b[bkey] += ', ' + mess_tab_list[tab]
                            else:
                                b[bkey] = ' Modified ' + mess_tab_list[tab]
                    break    
        for keyb in b:
            b[keyb] += ' \n'
        return b
    
    def find_key_in_dict(dic, key):
        check = False
        for i in dic:
            if i == key:
                check = True
        return check
        
        
    # delete mess_tab_list fields in vals and transfer to new dict
    def convert_new_dict(self, dic):
        dic_temp = dic.copy()
        temp = {}
        mess_tab_list = ["add_lines_module_effort", "add_lines_summary_totalcost", "add_lines_summary_costrate",
                         "add_lines_resource_effort", "add_lines_module_assumption", "add_lines_module_summary", "add_lines_module_breakdown"]
        for i in mess_tab_list:
            for key in dic_temp:
                if key == i:
                    temp[i] = dic.pop(key)
        return temp
            
    
    def get_values(self, est):
        vals_values = []
        mess_field = ["project_name",  "stage"] #"total_cost",
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids", "currency_id", "contract_id"] #, "message_main_attachment_id"
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