from odoo import models, fields, api, _
import json
from odoo.exceptions import UserError


class Estimation(models.Model):
    """
    Describes a work estimation.
    """
    _name = "estimation.work"
    _description = "Estimation"
    _rec_name = "number"

    project_name = fields.Char("Project Name", required=True)
    number = fields.Char("No", readonly=True, required=True, copy=False, index=False, default="New")

    estimator_ids = fields.Many2one('res.users', string='Estimator')
    reviewer_ids = fields.Many2one('res.users', string='Reviewer')
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True)
    currency_id = fields.Many2one("estimation.currency", string="Currency", required=True, default=1)
    currency_id_domain = fields.Char(compute="_compute_currency_id_domain", readonly=True, store=False,)
    project_type_id = fields.Many2one("project.type", string="Project Type", help="Please select project type ...")

    potential_budget = fields.Float(string="Potential Budget")
    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost')
    summary_currency_id = fields.Integer("Summarry Currency id", compute='_compute_summary_currency')
    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    project_code = fields.Char(string="Project Code", required=True,)
    description = fields.Text(string="Description", help="Description estimation")
    stage = fields.Selection([("new","New"), 
                              ("created","Created"),
                              ("approved","Approved"),
                              ("reject","Reject"),
                              ("updated","Updated"),
                              ("in_progress","In Progress"), 
                              ("completed","Completed"),
                              ("pending","Pending")], 
                            string="Status", 
                            required=True)
    
    sequence_module = fields.Integer(string="Sequence Module", store=True, default = 1, compute ='_compute_sequence_module') # for compute sequence module
    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'connect_summary', string='Summary Total Cost')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'connect_summary_costrate', string='Summary Cost Rate')
    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'estimation_id', string='Resource Planning Effort')
    add_lines_module = fields.One2many('estimation.module', 'estimation_id', domain="[('estimation_id', '=', 4)]", string="Modules")
   
    check_generate_project= fields.Boolean(default=False, compute='action_generate_project', store=True)

    @api.depends('currency_id')
    def _compute_summary_currency(self):
        self.summary_currency_id = self.currency_id
        summary_cost_rate = self.env['estimation.summary.costrate'].search([('connect_summary_costrate', '=', self.ids)])
        for item in summary_cost_rate:
            item.currency_ids = self.summary_currency_id

    @api.depends('currency_id')
    def _compute_currency_id_domain(self):
        currency_name = ['VND', 'USD', 'JPY']
        currency_ids = self.env['estimation.currency'].search([('name', 'in', currency_name)]).ids
        self.currency_id_domain = json.dumps(
                [('id', 'in', currency_ids)]
            )

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
        
        #for CRM
        active_id = self._context.get('active_id')
        if active_id:
            estimation_lead = self.env['crm.lead'].search([('id', '=', active_id)])
            estimation_lead.estimation_count += 1
        return result

    # Automatically load 12 activities and module summary data when creating an estimation
    @api.model
    def default_get(self, fields):
        res = super(Estimation, self).default_get(fields)
        get_data_cost_rate = self.env['config.job.position'].search([])
        summary_total_cost_line = []
        cost_rate_line = []

        # TODO missing add many module
        # get_data_summary_total_cost = self.env['estimation.summary.totalcost'].search([])
        # for record in get_data_summary_total_cost:
        content = {
            'connect_summary': '',
            'sequence': 1,
            'module': 'Module 1',
            'design_effort': 0.0,
            'dev_effort': 0.0,
            'tester_effort': 0.0,
            'comtor_effort': 0.0,
            'brse_effort': 0.0,
            'pm_effort': 0.0,
            'total_effort': 0.0,
            'cost': 0.0
        }
        line = (0, 0, content)
        summary_total_cost_line.append(line)

        for re in get_data_cost_rate:
            cost_rate = self.env['cost.rate'].search([('job_type', '=', re.job_position)])
            role_default = cost_rate[0]
            content = {
                'sequence': re.sequence,
                'types': re.job_position,
                'role': role_default,
                'yen_month': 0.0,
                'yen_day': 0.0,

            }
            line = (0, 0, content)
            cost_rate_line.append(line)

        res.update({
            'add_lines_summary_totalcost': summary_total_cost_line,
            'add_lines_summary_costrate': cost_rate_line,
        })
        return res
    
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
        # ls_keys = ["reviewer_ids", "customer_ids", "currency_id", "estimator_ids", "project_type_id"]   because only fields  in vals have id
        for item in vals:
            if item == "reviewer_ids" and vals[item] != '':
                vals[item] = self.env['res.users'].search([('id','=',vals[item])]).name
            elif item == "customer_ids" and vals[item] != '':
                vals[item] = self.env['res.partner'].search([('id','=',vals[item])]).name
            elif item == "currency_id" and vals[item] != '':
                vals[item] = self.env['estimation.currency'].search([('id','=',vals[item])]).name
            elif item == "estimator_ids" and vals[item] != '':
                vals[item] = self.env['res.users'].search([('id','=',vals[item])]).name
            elif item == "project_type_id" and vals[item] != '':
                vals[item] = self.env['project.type'].search([('id','=',vals[item])]).name
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
                         'add_lines_module': 'Modules',
                         'add_lines_module_assumption': 'Assumption', 
                         'add_lines_module_summary': 'Summary', 
                         'add_lines_module_effort_distribute_activity': 'Effort Distribution',
                         'add_lines_module_activity': 'Work Breakdown Structure and Estimate',
                         'total_manday': 'Total (mandays)'}
        key_output = {'add_lines_summary': 'Summary', 'add_lines_resource': 'Resource Planning', 'add_lines_module': 'Module', 'total_manday': 'Module'}
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
        mess_tab_list = ["add_lines_module_effort_distribute_activity", "add_lines_summary_totalcost", "add_lines_summary_costrate",
                         "add_lines_resource_effort", "add_lines_module_assumption", "add_lines_module_summary", "add_lines_module_activity", 
                         "total_manday", "check_generate_project", 'add_lines_module'] # add total_manday field as it is not needed to track changes
        for i in mess_tab_list:
            for key in dic_temp:
                if key == i:
                    temp[i] = dic.pop(key)
        return temp
    
    def get_values(self, est):
        vals_values = []
        mess_field = ["project_name",  "stage", "project_code", "description"] # List type String
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids", "currency_id", "project_type_id"] # List type Int (id)
        mess_field_date = ["sale_date", "deadline"] #List type Date
       
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

    # @api.depends('currency_id')
    # def _compute_total_cost(self):
    #     for item in self:
    #         item.total_cost = self.env['estimation.summary.totalcost'].search([('connect_summary', '=', item.id)]).cost

    def action_generate_project(self):
        for estimation in self:
            if not estimation.estimator_ids:
               raise UserError('Please select an estimator before generating project.')
            project = self.env['project.project'].sudo().create({
                'name': estimation.project_name,
                'user_id':estimation.estimator_ids.id
            })
            activity = self.env['config.activity'].search([('estimation_id','=',estimation.id)])
            for act in activity:
                for breakdown in self.env['module.breakdown.activity'].search([('activity_id','=',act.id)]):
                    self.env['project.task'].create({
                        'project_id':project.id,
                        'stage_id':self.env['project.task.type'].search([('name','=','Backlog')])[0].id,
                        'name':breakdown.activity,
                        'user_ids':[],
                        'issues_type':1,
                        'status':2,
                        'planned_hours':breakdown.mandays * 8
                    })
            estimation.check_generate_project = True
            return project


    @api.depends('add_lines_module')
    def _compute_sequence_module(self):
        max_sequence = 0
        modules = self.env['estimation.module'].search([('estimation_id', '=', self.id or self.id.origin)])
        #if there is data and a new record is created
        if modules:
            for item in modules:
                if item.sequence > max_sequence:
                    max_sequence = item.sequence
            Estimation.content_compute(self, max_sequence)

        #if no data exists and a new record is created
        else:
            max_sequence = 1
            Estimation.content_compute(self, max_sequence)
                    
    def content_compute(self, max_sequence):
        for record in self:
            record.sequence_module = max_sequence   # This is required
            # if a new record is created
            if record.add_lines_module:
                re_max_sequence = 0
                for rec in record.add_lines_module: 
                    if rec.sequence > re_max_sequence:
                        re_max_sequence = rec.sequence
                max_sequence = re_max_sequence + 1
                record.sequence_module = max_sequence  # This is required
     
    def unlink(self):
        for record in self:
            record.add_lines_overview.unlink()
            record.add_lines_summary_totalcost.unlink()
            record.add_lines_summary_costrate.unlink()
            record.add_lines_resource_effort.unlink()
            record.add_lines_module.unlink()
        return super(Estimation, self).unlink()  
class Lead(models.Model):
    _inherit = ['crm.lead']

    estimation_count = fields.Integer(string='# Registrations')
