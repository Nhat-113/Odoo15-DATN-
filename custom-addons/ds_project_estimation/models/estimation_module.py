from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import json, string, uuid

class EstimationModule(models.Model):
    _name = "estimation.module"
    _description ="Estimation List Modules"
    _rec_name = "component"
    _order = "sequence"
    
    sequence = fields.Integer(string="No", index=True)
    component = fields.Char(string="Components", required=True)
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays") 
    check_compute = fields.Char(string="Check", readonly=True)
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

    get_estimation_id = fields.Integer(string="Estimation Id")
    key_primary = fields.Char(string="Key unique module")
    get_module_activate = fields.Char(string="Module activate", compute='_compute_get_modules', store=True)
    check_save_estimation = fields.Boolean(string="Check save estimation", default=False, store=True)
    
    @api.depends('component')
    def _compute_get_modules(self):
        for record in self:
            record.estimation_id.module_activate = record.component
            if record.component != '':
                record.get_module_activate = record.component
            else:
                record.component = record.get_module_activate
            
            #check modified components name
            modules = self.env['estimation.module'].search([('key_primary', '=', record.key_primary)])
            for item in modules:
                if item.component != record.component and record.check_save_estimation == False:
                    item.write({'component': record.component})
            
            
    def write(self, vals):
        result = super(EstimationModule, self).write(vals)
        if 'estimation_id' in vals:
            module_name = []
            for item in self:
                item.check_save_estimation = True
                module_name.append(item.component)

            #write message description to overview
            self._overview_autolog_description(module_name, ' has been created successfully!')

            modules = self.env['estimation.module'].search([('estimation_id', '=', vals['estimation_id'])])
            for module in self.estimation_id.add_lines_summary_totalcost:
                for module_tab in modules:
                    if module.key_primary == module_tab.key_primary:
                        module_tab.sequence = module.sequence
                        
        #delete cosrate when modified module name
        if 'component' in vals:
            for module in self:
                cost_rate_db = self.env["estimation.summary.costrate"].search([('key_primary', '=', module.key_primary)])
                for costrate in cost_rate_db:
                    if costrate.name != vals['component']:
                        costrate.unlink()
        return result


    def unlink(self):
        module_name = []
        for record in self:
            record.module_assumptions.unlink()
            record.module_summarys.unlink()
            record.module_effort_activity.unlink()
            record.module_config_activity.unlink()
            
            module_name.append(record.component)
        #write message description to overview
        self._overview_autolog_description(module_name, ' was deleted successfully!')
        
            # record.summary_total_cost.unlink()
            # record.summary_cost_rate.unlink()
        return super(EstimationModule, self).unlink()
    
    def _overview_autolog_description(self, module_name, message):
        if len(self.estimation_id.add_lines_overview) != 0:
            descriptions = 'Module '
            max_revision = max(item.revision for item in self.estimation_id.add_lines_overview)
            for des in self.estimation_id.add_lines_overview:
                if des.revision == max_revision:
                    for index in range(len(module_name)):
                        descriptions += module_name[index]
                        if index < len(module_name) - 1:
                            descriptions += ', '
                    des.description = descriptions + message
                
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
            'module_summarys': summary_line,
            'check_compute': 'OK'  #is required for compute sequence
        })
        return res
    
    def _random_key_connect_activity(self):
        key = str(uuid.uuid4())
        return key

    
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
        self.key_primary = self._random_key_connect_activity()
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