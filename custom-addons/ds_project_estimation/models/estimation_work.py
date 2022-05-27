from email.policy import default
import string

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

    estimator_ids = fields.Many2one('res.users', string='Estimator')
    reviewer_ids = fields.Many2one('res.users', string='Reviewer')
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True)
    currency_id = fields.Many2one("res.currency", string="Currency")
    project_type_id = fields.Many2one("project.type", string="Project Type", help="Please select project type ...")

    expected_revenue = fields.Float(string="Expected Revenue")
    total_cost = fields.Float(string="Total Cost (YEN)", compute='_compute_total_cost')
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays")
    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    project_code = fields.Char(string="Project Code", required=True)
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
    
    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'connect_summary', string='Summary Total Cost')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'connect_summary_costrate', string='Summary Cost Rate')
    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'connect_resource_plan', string='Resource Planning Effort')
    add_lines_module_assumption = fields.One2many('estimation.module.assumption', 'connect_module', string='Module Assumption')
    add_lines_module_summary = fields.One2many('estimation.module.summary', 'estimation_id', string='Module Summary')
    add_lines_module_activity = fields.One2many('config.activity', 'estimation_id', string="Breakdown Structure")
    add_lines_module_effort_distribute_activity = fields.One2many('module.effort.activity', 'estimation_id', string='Module Effort')

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

    # Automatically load 12 activities and module summary data when creating an estimation
    @api.model
    def default_get(self, fields):
        res = super(Estimation, self).default_get(fields)
        get_data_activities = self.env['data.activity'].search([])
        get_data_cost_rate = self.env['config.job.position'].search([])
        data_summary = self.env['data.module.summary'].search([])
        activities_line = []
        activities_effort_line = []
        summary_line = []
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
            content = {
                'sequence': re.sequence,
                'types': re.job_position,
                'role': '',
                'yen_month': 0.0,
                'yen_day': 0.0,
                'vnd_day': 0.0
            }
            line = (0, 0, content)
            cost_rate_line.append(line)

        for record in get_data_activities:
            content = {
                'sequence': record.sequence, 
                'activity': record.activity,
                'effort': 0.0,
                'percent': 0.0,
                'activity_type': record.activity_type
            }
            line = (0, 0, content)
            activities_line.append(line)
            
            temp = content.copy()
            temp.pop('activity_type')
            line_effort = (0, 0, temp)
            activities_effort_line.append(line_effort)
        
        for item in data_summary:
            line = (0, 0, {
                'summary_type': item.summary_type,
                'description' : item.description,
                'value': item.value,
                'type': item.type
            })
            summary_line.append(line)
        
        res.update({
            'add_lines_module_summary': summary_line,
            'add_lines_module_activity': activities_line,
            'add_lines_module_effort_distribute_activity': activities_effort_line,
            'add_lines_summary_totalcost': summary_total_cost_line,
            'add_lines_summary_costrate': cost_rate_line
        })
        return res
    
    @api.depends('add_lines_module_activity.effort')
    def _compute_total_mandays(self):
        ls_activity = self.env['config.activity'].search([('estimation_id', '=', self.id)])
        total = 0.0
        for item in ls_activity:
            total += item.effort
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
        # ls_keys = ["reviewer_ids", "customer_ids", "currency_id", "estimator_ids", "project_type_id"]   because only fields  in vals have id
        for item in vals:
            if item == "reviewer_ids" and vals[item] != '':
                vals[item] = self.env['res.users'].search([('id','=',vals[item])]).name
            elif item == "customer_ids" and vals[item] != '':
                vals[item] = self.env['res.partner'].search([('id','=',vals[item])]).name
            elif item == "currency_id" and vals[item] != '':
                vals[item] = self.env['res.currency'].search([('id','=',vals[item])]).name
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
                         "total_manday"] # add total_manday field as it is not needed to track changes
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
    
    def action_refresh_estimation(self):
        # refresh total mandays in estimation work
        ls_activity = self.env['config.activity'].search([('estimation_id', '=', self.id)])
        total = 0.0
        for item in ls_activity:
            total += item.effort
        for record in self:
            #if total mandays not modify -> nothing to do
            if record.total_manday != total:
                record.total_manday = total
            
        # refresh Percentage in Effort distribution activity
        ls_effort_distribute = self.env['module.effort.activity'].search([('estimation_id', '=', self.id)])
        total_effort = 0.0        
        for record in ls_effort_distribute:
            total_effort += record.effort
        for record in ls_effort_distribute:
            if total_effort != 0.0:
                record.percent = round((record.effort / total_effort ) * 100, 2 )
            else:
                record.percent = total_effort
        
        # refresh total effort of the module breakdown activity
        ls_break = self.env['module.breakdown.activity'].search([])
        for record in ls_activity:
            final_manday = 0.0
            for item in ls_break:
                if item.activity_id and (record.id == item.activity_id.id):
                    if item.type == 'type_2':
                        final_manday += item.mandays
                    elif item.type == 'type_3':
                        final_manday += item.persons * item.days
                    elif item.type == 'type_1':
                        if record.activity_current:
                            item.mandays = round((item.percent_effort * record.activity_current.effort)/ 100, 2)
                        else:
                            item.mandays = 0
                        final_manday += item.mandays 
            record.effort = final_manday
        
        # compute summary module
        module_summary = self.env['estimation.module.summary']
        days_per_month = module_summary.search([('estimation_id', '=', self.id), ('type', '=', 'default_per_month')])
        ls_module_summary = module_summary.search([('estimation_id', '=', self.id)])
        for record in ls_module_summary:
            if record.type == 'man_day':
                record.value = self.total_manday
            elif record.type =='man_month':
                record.value = round(self.total_manday / days_per_month.value, 2)
        return

    def _compute_total_cost(self):
        for se in self:
            se.total_cost = self.env['estimation.summary.totalcost'].search([('connect_summary', '=', se.id)]).cost

