from ast import literal_eval
import time
from odoo import models, fields, api, _
import json
from odoo.exceptions import UserError, ValidationError


class Estimation(models.Model):
    """
    Describes a work estimation.
    """
    _name = "estimation.work"
    _description = "Estimation"
    _rec_name = "number"

    project_name = fields.Char("Project Name", required=True)
    number = fields.Char("No", readonly=True, required=True, copy=False, index=True, default='New')

    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    estimator_ids = fields.Many2one('res.users', string='Estimator')
    reviewer_ids = fields.Many2one('res.users', string='Reviewer')
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True, domain="[('is_company','=','true')]")
    currency_id = fields.Many2one("estimation.currency", string="Currency", required=True, domain="[('is_active', '=', True)]")
    project_type_id = fields.Many2one("project.type", string="Project Type", help="Please select project type ...", required=True)
    department_id = fields.Many2one("hr.department", string="Department", domain="[('company_id','=', company_id)]")

    # potential_budget = fields.Float(string="Potential Budget")
    total_cost = fields.Float(string="Total Cost", store=True, compute='_compute_total_cost')
    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    project_code = fields.Char(string="Project Code", required=True,)
    description = fields.Text(string="Description", help="Description estimation")
    stage = fields.Many2one('estimation.status', string="Status", required=True)
    domain_stage = fields.Char(string="Stage domain", readonly=True, store=False, compute='_compute_domain_stage')
    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_module = fields.One2many('estimation.module', 'estimation_id', string="Modules")
    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'estimation_id', string='Summary Total Cost')
    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'estimation_id', string='Resource Planning Effort')
    resource_plan_result_effort = fields.One2many('estimation.resource.plan.result.effort', 'estimation_id')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'estimation_id',
                                                 string='Summary Cost Rate')


    gantt_view_line = fields.One2many('gantt.resource.planning', 'estimation_id', string="Gantt")
    check_generate_project = fields.Boolean(default=False, compute='action_generate_project', store=True)


    @api.onchange('currency_id')
    def _compute_domain_stage(self):
        for record in self:
            if self.user_has_groups('ds_project_estimation.estimation_access_administrator'):
                record.domain_stage = json.dumps([('type', '!=', False)])
            elif self.user_has_groups('ds_project_estimation.estimation_access_director') \
                or self.user_has_groups('ds_project_estimation.estimation_access_sale_leader'):
                    record.domain_stage = json.dumps([('type', 'in', ['completed', 'pending', 'approved', 'reject'])])
            elif self.user_has_groups('ds_project_estimation.estimation_access_officer'):
                record.domain_stage = json.dumps([('type', 'in', ['created', 'updated', 'in_progress'])])
            else:
                record.domain_stage = json.dumps([('type', 'in', ['new', 'completed', 'pending'])])


    @api.model
    def create(self, vals):
        vals_over = {'connect_overview': '', 'description': ''}
        if vals.get("number", 'New') == 'New':
            vals["number"] = self.env["ir.sequence"].next_by_code("estimation.work") or 'New'
        result = super(Estimation, self).create(vals)
        vals_over["connect_overview"] = result.id
        vals_over["description"] = 'Create New Estimation'
        self.env["estimation.overview"].create(vals_over)

        # #for CRM
        # active_id = self._context.get('active_id')
        # if active_id:
        #     estimation_lead = self.env['crm.lead'].search([('id', '=', active_id)])
        #     estimation_lead.estimation_count += 1

        return result

    def write(self, vals):
        vals_over = {'connect_overview': self.id, 'description': ''}
        if vals:
            est_new_vals = vals.copy()
            ls_message_values = self.env['estimation.work'].search([('id','=',self.id or self.id.origin)])
            est_old_vals = self.get_values(ls_message_values)
            vals_tab_module = self.convert_new_dict(est_new_vals)
            est_desc_content = self.merge_dict_vals(est_old_vals, est_new_vals, vals_tab_module)
            est_desc_content_convert = est_desc_content.copy()
            self.convert_field_to_field_desc(est_desc_content_convert)
            for key in est_desc_content_convert:
                if key == 'Generate Project ':
                    vals_over["description"] += key + est_desc_content_convert[key]
                else:
                    vals_over["description"] += key + ' : ' + est_desc_content_convert[key]

            if vals_over["description"] != '':
                check_click_module = self.skip_log_overview(vals)
                if len(vals) == 1 and 'add_lines_summary_totalcost' in vals and check_click_module == True:
                    vals_over.clear()
                else:
                    self.env["estimation.overview"].create(vals_over)
            result = super(Estimation, self).write(vals)
            return result
        
    def skip_log_overview(self, vals):
        if 'add_lines_summary_totalcost' in vals and len(vals) == 1:
            for item in vals['add_lines_summary_totalcost']:
                if type(item[2]) == dict:
                    if 'check_activate' in item[2] and len(item[2]) == 1:
                        return True
            return False
                            
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
            elif item == "stage" and vals[item] != '':
                vals[item] = self.env['estimation.status'].search([('id','=',vals[item])]).status
            elif item == "company_id" and vals[item] != '':
                vals[item] = self.env['res.company'].search([('id','=',vals[item])]).name
            elif item == "department_id" and vals[item] != '':
                vals[item] = self.env['hr.department'].search([('id','=',vals[item])]).name
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
                         'check_generate_project': 'Success'}
        key_output = {'add_lines_summary': 'Summary', 'add_lines_resource': 'Resource Planning', 'add_lines_module': 'Module', 'check_generate_project': 'Generate Project '}
        for key in vals_tab_module:
            for tab in mess_tab_list:
                if key == tab:
                    for op in key_output:
                        if tab.find(op) != -1:
                            bkey = key_output[op]
                            if Estimation.find_key_in_dict (b, bkey):
                                b[bkey] += ', ' + mess_tab_list[tab]
                            else:
                                if key == 'check_generate_project':
                                    b[bkey] = mess_tab_list[tab]
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
        mess_tab_list = ["add_lines_summary_totalcost", "add_lines_summary_costrate", "add_lines_resource_effort",
                        "check_generate_project", 'add_lines_module', 'module_activate']
        for i in mess_tab_list:
            for key in dic_temp:
                if key == i:
                    temp[i] = dic.pop(key)
        return temp
    
    def get_values(self, est):
        vals_values = []
        mess_field = ["project_name", "project_code", "description"] # List type String
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids",  "stage", "currency_id", "project_type_id", "company_id", "department_id"] # List type Int (id)
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
                    month = str(item[k].month)
                    day = str(item[k].day)
                    if item[k].month < 10:
                        month = str(0) + str(item[k].month)
                    if item[k].day < 10:
                        day = str(0) + str(item[k].day)
                    temp = str(item[k].year) + '-' + month + '-' + day
                    vals_values.append(temp)
                else:
                    vals_values.append('None')
        
        vals_key = mess_field + mess_field_obj + mess_field_date
        value = dict(zip(vals_key, vals_values))
        return value

    @api.depends('add_lines_summary_totalcost.cost')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = sum(item.cost for item in record.add_lines_summary_totalcost)
    

    def generate_project_cron(self):
        estimation_ids = self.env['ir.config_parameter'].sudo(
            ).get_param('gen_project_cron.records')
        estimations = self.env['estimation.work'].browse(literal_eval(estimation_ids))
        for estimation in estimations:
            project = self.env['project.project'].sudo().create({
                'name': estimation.project_name,
                'user_id':estimation.estimator_ids.id,
                'estimation_id': estimation.id,
                'department_id': estimation.department_id.id,
                'company_id': estimation.company_id.id,
                'project_type': estimation.project_type_id.id
            })
            modules = self.env['estimation.module'].search([('estimation_id', '=', estimation.id)])
            for module in modules:
                activity = self.env['config.activity'].search([('module_id','=',module.id)])
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
        self.env['ir.config_parameter'].sudo().set_param(
            'gen_project_cron.records', [])

        return {}

    def action_generate_project(self):
        for estimation in self:
            if not estimation.estimator_ids:
               raise UserError('Please select an estimator before generating project.')

            # set global variable for self' records
            self.env['ir.config_parameter'].sudo().set_param(
                'gen_project_cron.records', self.ids)
            ir_cron = self.env.ref('ds_project_estimation.gen_project_cron')
            ir_cron.write(
                {'active': True, 'nextcall': fields.datetime.now()})
            message_id = self.env['estimation.message.wizard'].create(
                {'message': _("In the next few minutes, project will be generate.")})
                
            estimation.check_generate_project = True
            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'estimation.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }

    
    def unlink(self):
        for record in self:
            record.add_lines_summary_totalcost.unlink()
            record.add_lines_summary_costrate.unlink()
            record.add_lines_resource_effort.unlink()
            record.add_lines_module.unlink()
            record.add_lines_overview.unlink()
            record.resource_plan_result_effort.unlink()
            record.gantt_view_line.unlink()
        return super(Estimation, self).unlink()  
    
# class Lead(models.Model):
#     _inherit = ['crm.lead']

#     estimation_count = fields.Integer(string='# Registrations')



class EstimationStatus(models.Model):
    _name = "estimation.status"
    _description = "Estimation Status"
    _rec_name = "status"
    
    status = fields.Char('Status')
    type = fields.Char('Type')