from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import uuid

class EstimationModule(models.Model):
    _name = "estimation.module"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description ="Estimation List Modules"
    _rec_name = "component"
    _order = "sequence"
    
    
    def _random_key_connect_activity(self):
        key = str(uuid.uuid4())
        return key
    
    
    sequence = fields.Integer(string="No", index=True)
    component = fields.Char(string="Components", required=True)
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays", tracking=True) 
    sequence_activities = fields.Integer(string="Sequence Activities", store=True, default=1, compute ='_compute_sequence_activities')
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    module_assumptions = fields.One2many('estimation.module.assumption', 'module_id')
    module_summarys = fields.One2many('estimation.module.summary', 'module_id')
    module_config_activity = fields.One2many('config.activity', 'module_id')
    module_effort_activity = fields.One2many('module.effort.activity', 'module_id')
    project_activity_type = fields.Selection([
                            ('base', 'Project Base'), 
                            ('odc', 'ODC')],
                            default='base',
                            required=True,
                            string="Template Project Type")

    key_primary = fields.Char(string="Key unique module")
            
    
    @api.model
    def create(self, vals):
        if 'key_primary' not in vals:
            key_unique = self._random_key_connect_activity()
            vals['key_primary'] = key_unique
        
        modules = self.env['estimation.module'].search([('estimation_id', '=', vals['estimation_id'])], limit=1, order='id DESC')
        next_sequence = modules.sequence + 1 if modules else 1
        vals['sequence'] = next_sequence
        
        self.validate_unique_module_component(vals['component'], vals['estimation_id'], self.id)
        result = super(EstimationModule, self).create(vals)
        
        self.action_create_data_mutil_models(vals, result.estimation_id.currency_id.name)
        result._overview_autolog_description(module_name = vals['component'], 
                                            message = ' has been created successfully!', 
                                            action = 'new')
        
        return result
            
    def action_create_data_mutil_models(self, vals, currency_name):
        new_vals = {
            'estimation_id': vals['estimation_id'],
            'sequence': vals['sequence'],
            'name': vals['component'],
            'key_primary': vals['key_primary']
        }
        self.env['estimation.resource.effort'].create(new_vals)
        total_cost_id = self.env['estimation.summary.totalcost'].create(new_vals)
        
        costrates = self.env['cost.rate'].search([])
        ls_fields = self.get_currency_fields_costrate()
        for index, record in enumerate(costrates):
            currency_est = ''
            for field in ls_fields:
                if ls_fields[field] == currency_name:
                    currency_est = field
                    break
            
            data = {
                'estimation_id': vals['estimation_id'],
                'total_cost_id': total_cost_id.id,
                'sequence': index + 1,
                'name': vals['component'],
                'job_position': record.job_type.id,
                'yen_month': record[currency_est],
                'key_primary': vals['key_primary']
            }
            self.env['estimation.summary.costrate'].create(data)
            
        #create total MD, MM record for resource planning
        is_exist_record = self.env['estimation.resource.plan.result.effort'].search([('estimation_id', '=', vals['estimation_id'])])
        if not is_exist_record:
            cnt = 1
            while cnt <= 2:
                lines = {
                    'estimation_id': vals['estimation_id'],
                    'sequence': cnt,
                    'name': 'Total (MD)' if cnt == 1 else 'Total (MM)',
                    'total_effort': 0,
                    'key_primary': 'totalmd' if cnt == 1 else 'totalmm'
                }
                self.env['estimation.resource.plan.result.effort'].create(lines)
                cnt += 1
        
    def get_currency_fields_costrate(self):
        fields = self.env['cost.rate'].fields_get()
        ls_fields = {}
        for field in fields:
            if fields[field]['type'] == 'float':
                ls_fields[field] = field.replace('x_cost_', '').upper()
        return ls_fields
        
    def create_resource_planning_gantt(self, estimation_id):
        gantts = self.env['gantt.resource.planning'].search([('estimation_id', '=', estimation_id)])
        if not gantts:
            job_positions = self.env['config.job.position'].search([])
            for record in job_positions:
                vals = {
                    'estimation_id': estimation_id,
                    'job_position_id': record.id,
                }
                self.env['gantt.resource.planning'].create(vals)
        
    
    def validate_unique_module_component(self, module_name, estimation_id, current_module):
        modules = self.search([('estimation_id', '=', estimation_id), ('component', '=', module_name), ('id', '!=', current_module)])
        if modules:
           raise ValidationError(_("Module '%(module_name)s' already exists", module_name = module_name) )
        
        
    def write(self, vals):
        if 'component' in vals:
            self.validate_unique_module_component(vals['component'], self.estimation_id.id, self.id)
            self.common_modify_module_values(self.estimation_id.add_lines_summary_totalcost, 'name', vals['component'])
            self.common_modify_module_values(self.estimation_id.add_lines_summary_costrate, 'name', vals['component'])
            self.common_modify_module_values(self.estimation_id.add_lines_resource_effort, 'name', vals['component'])

        # Reset sequence module when deleting any module
        if 'sequence' in vals:
            self.common_modify_module_values(self.estimation_id.add_lines_resource_effort, 'sequence', vals['sequence'])
            self.common_modify_module_values(self.estimation_id.add_lines_summary_totalcost, 'sequence', vals['sequence'])
        
        self._overview_autolog_description(vals, 'Modified module ' + self.component + ':', 'write')
        
        result = super(EstimationModule, self).write(vals)
        return result
    
    
    def common_modify_module_values(self, datas, field_key, value):
        for record in datas:
            if record.key_primary == self.key_primary:
                record[field_key] = value
        


    def unlink(self):
        module_name = ''
        estimation_id = self.estimation_id.id
        cnt = 0
        for record in self:
            # module_name.append(record.component)
            if cnt > 0 and cnt < len(self):
                module_name += ', '
            module_name += record.component
            record.module_assumptions.unlink()
            record.module_summarys.unlink()
            record.module_effort_activity.unlink()
            record.module_config_activity.unlink()
            
            record.common_remove_module_multi_model(record.estimation_id.add_lines_summary_totalcost)
            record.common_remove_module_multi_model(record.estimation_id.add_lines_resource_effort)
            record.common_remove_module_multi_model(record.estimation_id.add_lines_summary_costrate)
            cnt += 1
            
        #write message description to overview
        self._overview_autolog_description(module_name, ' was deleted successfully!', action = 'delete')
        result = super(EstimationModule, self).unlink()
        self.common_auto_reset_sequence_module(estimation_id)
        return result
    
    def common_remove_module_multi_model(self, datas):
        for record in datas:
            if record.key_primary == self.key_primary:
                record.unlink()
                
    def common_auto_reset_sequence_module(self, estimator_id):
        modules = self.search([('estimation_id', '=', estimator_id)], order='sequence')
        for index, record in enumerate(modules):
            record.write({
                'sequence': index + 1
            })
    
    def _overview_autolog_description(self, module_name, message, action):
        overview = self.env['estimation.overview']
        next_revision = self.estimation_id.add_lines_overview[0].revision + 0.1
        if action in ['new', 'delete']:
            des = 'Module ' + module_name + message
            overview.create({
                'connect_overview': self.estimation_id.id,
                'revision': next_revision,
                'description': des
            })
        else:
            # with write action, module_name = vals
            if 'component' in module_name:
                message += '\n\t- Component module: ' + self.component + ' --> ' + module_name['component']
            if 'project_activity_type' in module_name:
                project_type_before = 'ODC' if self.project_activity_type == 'odc' else 'Project Base'
                project_type_after = 'ODC' if module_name['project_activity_type'] == 'odc' else 'Project Base'
                message += '\n\t- Template Project Type: ' + project_type_before + ' --> ' + project_type_after
            
            if 'component' not in module_name and 'project_activity_type' not in module_name:
                return
            else:
                overview.create({
                    'connect_overview': self.estimation_id.id,
                    'revision': next_revision,
                    'description': message
                })
                
                
    @api.constrains('module_config_activity')
    def check_modify_activity(self):
        self.message_post(body=_("Effort distribution: The content has been modified"))
        
    @api.constrains('module_assumptions')
    def post_message_history_assumption(self):
        self.message_post(body=_("Assumption: The content has been modified"))
    
                
    @api.model
    def default_get(self, fields):
        res = super(EstimationModule, self).default_get(fields)
        data_summary = self.env['data.module.summary'].search([])
        summary_line = []
        
        for item in data_summary:
            line = (0, 0, {
                'summary_type': item.summary_type,
                'description' : item.description,
                'value': item.value,
                'type': item.type
            })
            summary_line.append(line)
        
        res.update({
            'module_summarys': summary_line
        })
        return res
    

    
    def get_activities_project_type(self, get_data_activities, activities_line, activities_effort_line):
        if self.project_activity_type == 'base': 
            if len(self.module_config_activity) == 0:
                get_data_activities = get_data_activities.search([('project_type', '=', 'base')])
            else:
                get_data_activities = get_data_activities.search([('project_type', '=', 'base')], limit=1)
        else:
            get_data_activities = get_data_activities.search([('project_type', '=', 'odc')])
        for record in get_data_activities:
            activities = {
                'sequence': record.sequence, 
                'activity': record.activity,
                'effort': 0.0,
                'percent': 0.0,
                'activity_type': record.activity_type,
                'check_default': True,
                'key_primary': self._random_key_connect_activity() + str(record.sequence)
            }
            if self.project_activity_type != 'base':
                activities['sequence'] = len(self.module_config_activity) + 1
                if len(self.module_config_activity) != 0:
                    activity_name = self.check_load_duplicate_activity(activities['activity'])
                    activities['activity'] = activity_name
                
            elif self.project_activity_type == 'base' and len(self.module_config_activity) != 0:
                activities['sequence'] = len(self.module_config_activity) + 1
                activity_name = self.check_load_duplicate_activity('Activity ')
                
                activities['activity'] = activity_name
            activities_line.append((0, 0, activities))
            
            temp = activities.copy()
            temp.pop('activity_type')
            temp.pop('check_default')
            activities_effort_line.append((0, 0, temp))
            
    def check_load_duplicate_activity(self, activity_name):
        for index in range(len(self.module_config_activity)):
            activity_name_rs = activity_name + str(len(self.module_config_activity) + index + 1)
            if activity_name_rs not in (act.activity for act in self.module_config_activity):
                return activity_name_rs
            else:
                index += 1
    
    def compute_load_activities(self):
        get_data_activities = self.env['data.activity']
        activities_line = []
        activities_effort_line = []
        # self.key_primary = self._random_key_connect_activity()
        self.get_activities_project_type(get_data_activities, activities_line, activities_effort_line)                    
            
        for record in self:
            record.update({
                'module_config_activity': activities_line,
                'module_effort_activity': activities_effort_line
                })

    @api.depends('module_config_activity.effort')
    def _compute_total_mandays(self):
        for record in self:
            total = sum( item.effort for item in record.module_config_activity)
            record.total_manday = total
    

    @api.depends('module_config_activity')
    def _compute_sequence_activities(self):
       
        #re-compute mandays for module breakdown activities
        for record in self.module_config_activity:
            if record.activity_current and record.activity_type == 'type_1':
                effort_activity_current = 0
                for activity_current in self.module_config_activity:
                    activity_current_id = 0
                    if activity_current.id:
                        activity_current_id = activity_current.id
                    else:
                        activity_current_id = activity_current.id.origin
                    if record.activity_current.id == activity_current_id:
                        effort_activity_current = activity_current.effort
                for breakdown in record.add_lines_breakdown_activity:
                    breakdown.mandays_input = round((breakdown.percent_effort * effort_activity_current)/ 100, 2)
                    breakdown.mandays = breakdown.mandays_input
      
    @api.onchange('module_config_activity')
    def add_a_line_effort_distribute(self):
        for record in self:
            ls_data_effort_activity = self.env['module.effort.activity'].search([('module_id', '=', record.id or record.id.origin)])
            #check add line activity duplicate
            activity_name_arr = []
            for item in record.module_config_activity:
               activity_name_arr.append(item.activity)
            if len(activity_name_arr) != len(set(activity_name_arr)):  # check duplicate
                raise UserError('Activity name already exists!')
            
            for rec in record.module_config_activity:
                #check loop add line activity
                check_exist_in_self = False
                check_exist_in_data = False
                for item in record.module_effort_activity:
                    if rec.sequence == item.sequence:
                        check_exist_in_self = True
                for act in ls_data_effort_activity:
                    if rec.sequence == act.sequence:
                        check_exist_in_data = True
                if check_exist_in_self == False and check_exist_in_data == False:
                    EstimationModule._get_activities(rec, record)
                
            # Case: delete record
            self._delete_activities(record.module_effort_activity, record.module_config_activity)
            self._reset_sequence(record.module_effort_activity)
            self._reset_sequence(record.module_config_activity)
            
    def _get_activities(rec_activity, record_module):
        line = []
        rec_activity.sequence = record_module.sequence_activities
        effort_line = (0, 0, {
                'sequence': rec_activity.sequence,
                'activity': rec_activity.activity,
                'effort': rec_activity.effort,
                'module_id': record_module.id or record_module.id.origin,
        })
        line.append(effort_line)
        record_module.update({
            'module_effort_activity': line
        })

    def _delete_activities(self, ls_effort_activity, ls_config_activities):
        for record in ls_effort_activity:
            if record.key_primary not in [rec.key_primary for rec in ls_config_activities]:
                record.write({'module_id': [(2, record.module_id.id or record.module_id.id.origin)]})
        
                
    def _reset_sequence(self, ls_data):
        for index, item in enumerate(ls_data):
            item.sequence = index + 1

class EstimationModuleAssumption(models.Model):
    _name = "estimation.module.assumption"
    _description = "Module Assumption of each estimation"

    module_id = fields.Many2one("estimation.module", string="Module")
    assumption = fields.Text("Assumption")

class EstimationModuleSummary(models.Model):
    _name = "estimation.module.summary"
    _description = "Module Summary of each estimation"

    module_id = fields.Many2one("estimation.module", string="Module")
    summary_type = fields.Char(string="Summary Type")
    description = fields.Char(string="Working Time/Efforts")
    value = fields.Float(string="Value", store=True, compute='_compute_value')
    type = fields.Char(string="Type")
    
    @api.depends('module_id.total_manday')
    def _compute_value(self):
        man_day_val = 0.0
        day_per_month = 0
        for record in self:
            if record.type == 'man_day':
                record.value = record.module_id.total_manday
                man_day_val = record.module_id.total_manday
            elif record.type == 'default_per_month':
                record.value = 20
                day_per_month = record.value
            elif record.type == 'default_per_day':
                record.value = 8
        for record in self:
            if record.type == 'man_month':
                if day_per_month != 0:
                    record.value = round(man_day_val / day_per_month, 2)

class EstimationModuleSummaryData(models.Model):
    _name = "data.module.summary"
    _description = "Data Module Summary of each estimation"

    summary_type = fields.Char(string="Summary Type", readonly=True)
    description = fields.Char(string="Working Time/Efforts", readonly=True)
    value = fields.Float(string="Value", readonly=True)
    type = fields.Char(string="Type")

class BreakdownActivities(models.Model):
    """
    Describe breakdown activities
    """
    _name = "module.breakdown.activity"
    _description = "Module Breakdown of each activity"
    _order = "sequence,id"

    activity_id = fields.Many2one('config.activity', string="Connect Activity Module")
    sequence = fields.Integer(string="No", readonly=True, store=True, compute='_compute_sequence')
    activity = fields.Char("Activity", required=True)
    job_pos = fields.Many2one('config.job.position', string="Job Position", required=True)
    mandays = fields.Float(string="Expected result (man-days)", readonly=True, store=True, compute='_compute_mandays')
    persons = fields.Integer(string="Persons", default=0)
    days = fields.Float(string="Days", default=0)
    percent_effort = fields.Float(string="Percent Effort (%)", default=0.0)
    type = fields.Selection(string="Type", store=True, related='activity_id.activity_type')
    
    mandays_input = fields.Float(string="Expected (man-days)")
    check_compute = fields.Char(string="Check", readonly=True)

    @api.model
    def default_get(self, fields):
        result = super(BreakdownActivities, self).default_get(fields)
        result.update({'check_compute': 'OK'})
        return result
    
    
    @api.model
    def create(self, vals):
        result = super(BreakdownActivities, self).create(vals)
        estimation_id = result.activity_id.module_id.estimation_id
        key_primary = result.activity_id.module_id.key_primary
        gantt = self.env['gantt.resource.planning']
        cost_rate= self.env['estimation.summary.costrate']
        check_gantt = gantt.search([('estimation_id', '=', estimation_id.id), ('job_position_id', '=', result.job_pos.id)])
        check_cost_rate = cost_rate.search([('estimation_id', '=', estimation_id.id), 
                                            ('key_primary', '=', key_primary),
                                            ('job_position', '=', result.job_pos.id)])
        if not check_gantt:
            gantt.create({
                'estimation_id': estimation_id.id,
                'job_position_id': result.job_pos.id,
                'value_man_month': 0
            })
        if not check_cost_rate:
            total_cost = self.env['estimation.summary.totalcost'].search([('estimation_id', '=', estimation_id.id),
                                                                          ('key_primary', '=', key_primary)])
            costrates = self.env['cost.rate'].search([('job_type', '=', result.job_pos.id)])
            currency_est = ''
            ls_fields = self.env['estimation.module'].get_currency_fields_costrate()
            for field in ls_fields:
                if ls_fields[field] == estimation_id.currency_id.name:
                    currency_est = field
                    break
            cost_rate.create({
                'estimation_id': estimation_id.id,
                'total_cost_id': total_cost.id,
                'sequence': len(total_cost.summary_costrates) + 1,
                'name': result.activity_id.module_id.component,
                'job_position': result.job_pos.id,
                'yen_month': costrates[currency_est],
                'key_primary': key_primary
            })
        return result

    @api.depends('activity_id.activity_type', 'activity_id.activity_current', 'persons', 'days', 'percent_effort', 'mandays_input')
    def _compute_mandays(self):
        for record in self:
            if record.activity == False:
                record.activity = self.check_load_duplicate_activity(self.activity_id.add_lines_breakdown_activity, record.sequence )
            if len(record.job_pos) == 0:
                job_pos_id = self.env['config.job.position'].search([], limit=1)
                record.job_pos = job_pos_id.id
            if record.type == 'type_3':
                record.mandays = record.persons * record.days
                record.mandays_input = record.mandays
            elif record.type == 'type_1':
                if record.activity_id.activity_current:
                    #because only the parent element can get the changed value of the child element => get value effort of activity_curent from module parent
                    effort_activity_current = self._find_effort_activity_current(record.activity_id.module_id.module_config_activity, record.activity_id.activity_current)
                    # record.mandays = round((record.percent_effort * record.activity_id.activity_current.effort)/ 100, 2)
                    record.mandays = round((record.percent_effort * effort_activity_current)/ 100, 2)
                    record.mandays_input = record.mandays
                else:
                    record.mandays = 0
                    record.mandays_input = record.mandays
            else:
                record.mandays = record.mandays_input

    def check_load_duplicate_activity(self, ls_breaks, sequence):
        for index in range(len(ls_breaks)):
            activity_name_rs = 'Activity ' + str(sequence + index)
            if activity_name_rs not in (breakdown.activity for breakdown in ls_breaks):
                return activity_name_rs
            else:
                index += 1 

    def _find_effort_activity_current(self, ls_activity, activity_current):
        result_effort = 0
        for record in ls_activity:
            if record.activity == activity_current.activity:
                result_effort = record.effort
        return result_effort

    @api.depends('check_compute')
    def _compute_sequence(self):
        for index, breakdown in enumerate(self.activity_id.add_lines_breakdown_activity):
            breakdown.sequence = index + 1
                        
class EffortActivities(models.Model):
    _name = "module.effort.activity"
    _description = "Module effort distribute activity"
    _rec_name = "activity"
    _order = "sequence,id"
    
    module_id = fields.Many2one("estimation.module", string="Module")
    
    sequence = fields.Integer(string="No", index=True, store=True)
    activity = fields.Char(string="Activity")
    effort = fields.Float(string='Effort', compute='_compute_effort', store=True)
    percent = fields.Float(string="Percentage (%)", default=0, store=True, compute='_compute_percentage')
    key_primary = fields.Char(string="Key Connect activity effort")
    
    # compute_effort is required for the _compute_percentage method to work correctly
    @api.depends('module_id.module_config_activity.effort', 'module_id.module_config_activity.activity')
    def _compute_effort(self):
        for record in self:
            for rec in record.module_id.module_config_activity:
                if record.key_primary == rec.key_primary:
                    record.effort = rec.effort
                    record.activity = rec.activity
                    record.sequence = rec.sequence
            
    @api.depends('effort', 'module_id.module_config_activity')
    def _compute_percentage(self):
        #if delete config activities record (because module_effort_activity didn't load in time after deleting an config_activity) => get effort from module_config_activity
        total_effort = sum(rec.effort for rec in self.module_id.module_config_activity)
        for rec in self:
            if total_effort != 0.0:
                rec.percent = round((rec.effort / total_effort ) * 100, 2)
            else:
                rec.percent = total_effort