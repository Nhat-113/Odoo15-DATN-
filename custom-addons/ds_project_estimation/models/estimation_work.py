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

    estimator_ids = fields.Many2one('res.users', string='Estimator')
    reviewer_ids = fields.Many2one('res.users', string='Reviewer')
    customer_ids = fields.Many2one("res.partner", string="Customer", required=True, domain="[('is_company','=','true')]")
    currency_id = fields.Many2one("estimation.currency", string="Currency", required=True, default=1)
    currency_id_domain = fields.Char(compute="_compute_currency_id_domain", readonly=True, store=False,)
    project_type_id = fields.Many2one("project.type", string="Project Type", help="Please select project type ...")

    potential_budget = fields.Float(string="Potential Budget")
    total_cost = fields.Float(string="Total Cost", compute='_compute_total_cost', store=True)
    summary_currency_id = fields.Integer("Summarry Currency id", compute='_compute_summary_currency')
    sale_date = fields.Date("Sale Date", required=True)
    deadline = fields.Date("Deadline", required=True)
    project_code = fields.Char(string="Project Code", required=True,)
    description = fields.Text(string="Description", help="Description estimation")
    stage = fields.Many2one('estimation.status', string="Status", required=True)
    domain_stage = fields.Char(string="Stage domain", readonly=True, store=False, compute='_compute_domain_stage')
    module_activate = fields.Char('Module Activate', store=True)
    sequence_module = fields.Integer(string="Sequence Module", store=True, default=1)
    add_lines_overview = fields.One2many('estimation.overview', 'connect_overview', string='Overview')
    add_lines_summary_costrate = fields.One2many('estimation.summary.costrate', 'connect_summary_costrate',
                                                 string='Summary Cost Rate', domain=lambda self: self.compute_domain_cost_rate())

    add_lines_summary_totalcost = fields.One2many('estimation.summary.totalcost', 'estimation_id', string='Summary Total Cost')

    add_lines_resource_effort = fields.One2many('estimation.resource.effort', 'estimation_id', string='Resource Planning Effort')
    add_lines_module = fields.One2many('estimation.module', 'estimation_id', string="Modules")
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

    @api.depends('module_activate', 'add_lines_module.component')
    def compute_domain_cost_rate(self):
        for record in self:
            if record.id != False:
                if self.check_modifed_module_name() != []:
                    components =  self.check_modifed_module_name()
                    return [('name', 'in', components)]
                else: 
                    if record.module_activate:
                        return [('name', 'in', [record.module_activate])]
                    else:
                        return []
            return []

    def check_modifed_module_name(self):
        for record in self:
            modules = self.env['estimation.module'].search([('estimation_id', '=', record.id or record.id.origin)])
            module_activate = []
            for module in self.add_lines_module:
                if module.key_primary not in [module_db.key_primary for module_db in modules]:
                    module_activate.append(module.component)
                for module_db in modules:
                    if module.key_primary == module_db.key_primary and module.component != module_db.component:
                        module_activate.append(module.component)
            return module_activate

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
        
        #check module is saved
        for module in self.add_lines_module:
            module.check_save_estimation = True

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

            # Delete cost rate when delete module
            self.compute_delete_cost_rate(vals)
            
            #check module is saved
            for module in self.add_lines_module:
                module.check_save_estimation = True

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
                            
    def compute_delete_cost_rate(self, vals):
        module_delete = []
        for key in vals:
            if key == 'add_lines_module':
                for item in vals['add_lines_module']:
                    if item[0] == 2:
                        module_delete.append(item[1])

                component_delete = []
                estimation_id_delete = []
                for rec in self.env["estimation.module"].search([('id', 'in', module_delete)]):
                    component_delete.append(rec.key_primary)
                    estimation_id_delete.append(rec.estimation_id.id)
                self.env["estimation.summary.costrate"].search([('key_primary', 'in', component_delete),('connect_summary_costrate', 'in', estimation_id_delete)]).unlink()
                self.env["estimation.summary.costrate"].search([('connect_summary_costrate', '=', False)]).unlink()

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
        mess_field_obj = ["estimator_ids", "reviewer_ids", "customer_ids",  "stage", "currency_id", "project_type_id"] # List type Int (id)
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
        for item in self:
            total = 0
            estimation_module = self.env['estimation.summary.totalcost'].search([('estimation_id', '=', item.id)])
            for record in estimation_module:
                total += record.cost
            item.total_cost = total

    def generate_project_cron(self):
        estimation_ids = self.env['ir.config_parameter'].sudo(
            ).get_param('gen_project_cron.records')
        estimations = self.env['estimation.work'].browse(literal_eval(estimation_ids))
        for estimation in estimations:
            project = self.env['project.project'].sudo().create({
                'name': estimation.project_name,
                'user_id':estimation.estimator_ids.id,
                'estimation_id': estimation.id
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

    @api.onchange('add_lines_module')
    def _compute_check_module(self):
        
        for record in self:
            #check data no activity
            for module in record.add_lines_module:
                if len(module.module_config_activity) == 0:
                    raise UserError(_('The Load Activities button must be clicked before saving the "%(component)s" module!', component = module.component))

            #check duplicate components module
            self.check_duplicate_components(record.add_lines_module)
            self.env['estimation.module']._reset_sequence(record.add_lines_module)
            resource_line = []
            total_cost_line = []
            vals_cost_rate = []
            module_active_late = []

            for module in record.add_lines_module:
                if module.key_primary not in (resource.key_primary for resource in record.add_lines_resource_effort):
                    for resource in record.add_lines_resource_effort:
                        if resource.key_primary in ['Total (MD)', 'Total (MM)']:
                            resource.write({'estimation_id': (2, record.id or record.id.origin)})
                        
                    lines = (0, 0, {
                        'sequence': module.sequence, 
                        'name': module.component,
                        'key_primary': module.key_primary
                    })
                    module_active_late.append(module.component)
                    resource_line.append(lines)
                    self.add_record_md_mm_resource_plan(resource_line)
                    self.add_module_in_summary_tab(module, total_cost_line, vals_cost_rate)
                elif module.component not in (resource.name for resource in record.add_lines_resource_effort):
                    self.compute_component_module(module, record.add_lines_resource_effort)
                    self.compute_component_module(module, record.add_lines_summary_totalcost)
                    self.compute_module_name_costrate(module, record.add_lines_summary_costrate, vals_cost_rate)

            record.update({
                'add_lines_resource_effort': resource_line,
                'add_lines_summary_totalcost': total_cost_line,
                'add_lines_summary_costrate': vals_cost_rate
            })
            # if module.component not in [item.name for item in record.add_lines_summary_costrate]:
            #     record.write({'add_lines_summary_costrate': vals_cost_rate})
                  
            #case: Delete module using write method
            self._delete_modules(record.add_lines_module, record.add_lines_resource_effort,
                                       record.add_lines_summary_totalcost, record.add_lines_summary_costrate)
            
            self._reset_sequence_module(record.add_lines_module)
            self.env['estimation.module']._reset_sequence(record.add_lines_resource_effort)
            self.env['estimation.module']._reset_sequence(record.add_lines_summary_totalcost)
            
    
    def compute_component_module(self, module, ls):
        for record in ls:
            if record.key_primary == module.key_primary:
                record.name = module.component
                break

    def compute_module_name_costrate(self, module, ls_costrate, vals_cost_rate):
        if module.key_primary in (record.key_primary for record in ls_costrate):
            for record in ls_costrate:
                if record.key_primary == module.key_primary:
                    record.name = module.component
        else:
            costrate_db = self.env['estimation.summary.costrate'].search([('key_primary', '=', module.key_primary)])
            for record in costrate_db:
                if record.key_primary == module.key_primary:
                    lines = (0, 0, {
                        'sequence': record.sequence,
                        'name': module.component,
                        'types': record.types,
                        # 'role': record.role,
                        'yen_month': record.yen_month,
                        'yen_day': record.yen_day,
                        'key_primary': module.key_primary
                    })
                    vals_cost_rate.append(lines)   

    def _reset_sequence_module(self, ls_module):
        for index, module in enumerate(ls_module):
            module.write({'sequence': index + 1})

    def check_duplicate_components(self, ls_modules):
        components = []
        for record in ls_modules:
            components.append(record.component)
            
        if len(components) != len(set(components)):
            raise UserError('Component name already exists!')

    def add_record_md_mm_resource_plan(self, resource_line):
        lines_md = (0, 0, {
            'sequence': 0, 
            'name': 'Total (MD)',
            'key_primary': 'Total (MD)'
        })
        lines_mm = (0, 0, {
            'sequence': 0, 
            'name': 'Total (MM)',
            'key_primary': 'Total (MM)'
        })

        resource_line.append(lines_md)
        resource_line.append(lines_mm)
        
    def add_module_in_summary_tab(self, module, total_cost_line, vals_cost_rate):
        # Create Cost Rate
        lines_1 = (0, 0, {
                'sequence': 0,
                'name': module.component,
                'key_primary': module.key_primary
            })
        total_cost_line.append(lines_1)
        
        cost_rate_line = self.env['config.job.position'].search([])
        for index, val in enumerate(cost_rate_line):
            cost_rate = self.env['cost.rate'].search([('job_type', '=', val.job_position)], limit=1)
            currencies = {'cost_usd': 'USD', 'cost_vnd': 'VND', 'cost_yen': 'JPY'}
            for currency in currencies:
                if self.currency_id.name == currencies[currency]:
                    lines_2 = (0, 0, {
                        'connect_summary_costrate': self.id or self.id.origin,
                        'sequence': index + 1,
                        'name': module.component,
                        'types': val.job_position,
                        # 'role': cost_rate.id,
                        'yen_month': cost_rate[currency],
                        # 'yen_day': cost_rate[currency] / 20,
                        'key_primary': module.key_primary
                    })
                    vals_cost_rate.append(lines_2)    

    def _delete_modules(self, ls_module, ls_resource_plan, ls_total_cost, ls_costrate):
        for record in ls_resource_plan:
            domain = [(2, record.estimation_id.id or record.estimation_id.id.origin)]
            if len(ls_module) == 0:
                record.write({'estimation_id': domain})
            elif record.key_primary not in [rec.key_primary for rec in ls_module] + ['Total (MD)', 'Total (MM)']:
                record.write({'estimation_id': domain})

        for record in ls_total_cost:
            domain = [(2, record.estimation_id.id or record.estimation_id.id.origin)]
            if record.key_primary not in [rec.key_primary for rec in ls_module]:
                for costrate in ls_costrate:
                    if costrate.key_primary == record.key_primary:
                        costrate.write({'connect_summary_costrate': domain})
                record.write({'estimation_id': domain})
    
    def unlink(self):
        for record in self:
            record.add_lines_overview.unlink()
            record.add_lines_summary_totalcost.unlink()
            record.add_lines_summary_costrate.unlink()
            record.add_lines_resource_effort.unlink()
            record.add_lines_module.unlink()

            #delete costrate no active
            self.env['estimation.summary.costrate'].search([('connect_summary_costrate', 'in', [record.id, False])]).unlink()
        
        #delete module failed
        self._delete_module_failed()
        return super(Estimation, self).unlink()  
    
    def _delete_module_failed(self):
        #case: delete modules from db with estimation_id = False
        module_in_db = self.env['estimation.module'].search([('estimation_id', '=', False)])    #,('component', 'not in', [module.component for module in record.add_lines_module])
        cost_rate_db = self.env['estimation.summary.costrate'].search([('connect_summary_costrate', '=', False)])
        module_in_db.unlink()
        cost_rate_db.unlink()
    
# class Lead(models.Model):
#     _inherit = ['crm.lead']

#     estimation_count = fields.Integer(string='# Registrations')



class EstimationStatus(models.Model):
    _name = "estimation.status"
    _description = "Estimation Status"
    _rec_name = "status"
    
    status = fields.Char('Status')
    type = fields.Char('Type')
