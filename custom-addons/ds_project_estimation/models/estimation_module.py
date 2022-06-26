from odoo import models, fields, api
from odoo.exceptions import UserError

class EstimationModule(models.Model):
    _name = "estimation.module"
    _description ="Estimation List Modules"
    _rec_name = "component"
    _order = "sequence"
    
    sequence = fields.Integer(string="No", index=True, readonly=True, store=True, compute='_compute_sequence')
    component = fields.Char(string="Components", required=True)
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays") 
    check_compute = fields.Char(string="Check", readonly=True)
    sequence_activities = fields.Integer(string="Sequence Activities", store=True, default=1, compute ='_compute_sequence_activities')
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    module_assumptions = fields.One2many('estimation.module.assumption', 'module_id')
    module_summarys = fields.One2many('estimation.module.summary', 'module_id')
    module_config_activity = fields.One2many('config.activity', 'module_id')
    module_effort_activity = fields.One2many('module.effort.activity', 'module_id')
    # estimation_resource_plan = fields.One2many('estimation.resource.effort', 'module_id')
    
    get_estimation_id = fields.Integer(string="Estimation Id")
    

    def unlink(self):
        for record in self:
            record.module_assumptions.unlink()
            record.module_summarys.unlink()
            record.module_effort_activity.unlink()
            record.module_config_activity.unlink()
            
            # check_data_resource_plan = self.env['estimation.resource.effort'].search([('estimation_id', '=', record.estimation_id.id)])
            # gantt_resource_plan = self.env['gantt.resource.planning'].search([('estimation_id', '=', record.estimation_id.id)])
            # if check_data_resource_plan:
            #     count = len(check_data_resource_plan)
            #     if count == 3:  # there is 1 module and 2 record mm + md -> delete all record
            #         check_data_resource_plan.unlink()  # delete all record
                    
            #         if gantt_resource_plan:  # remove gantt
            #             gantt_resource_plan.unlink()
            #     elif count > 3: # there are many modules -> delete 1 record
            #         for item in check_data_resource_plan:
            #             if item.module_id.id == record.id:
            #                 item.unlink()
        return super(EstimationModule, self).unlink()
                
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
    
    def compute_load_activities(self):
        get_data_activities = self.env['data.activity'].search([])
        activities_line = []
        activities_effort_line = []
        for record in get_data_activities:
            content = {
                'sequence': record.sequence, 
                # 'sequence': 0, 
                'activity': record.activity,
                'effort': 0.0,
                'percent': 0.0,
                'activity_type': record.activity_type,
                'check_default': True
            }
            line = (0, 0, content)
            activities_line.append(line)
            
            temp = content.copy()
            temp.pop('activity_type')
            temp.pop('check_default')
            line_effort = (0, 0, temp)
            activities_effort_line.append(line_effort)
            
        for record in self:
            if record.estimation_id:    # nếu module đã được lưu trước đó với 1 estimation đã tồn tại
                for rec in record.estimation_id.add_lines_module:
                    if rec.id == record.id:
                        record.sequence = rec.sequence
                        record.component = rec.component
            else:   # nếu module chưa được lưu
                module_db = self.env['estimation.module']
                max_sequence = max_exist_data = max_not_data = 0
                # kiểm tra xem đã tồn tại module nào trong estimation chưa hoặc estimation đã tồn tại chưa
                ls_exist_datas = module_db.search([('estimation_id', '=', record.get_estimation_id)])
                if ls_exist_datas:
                    max_exist_data = max(item.sequence for item in ls_exist_datas)
                
                # kiểm tra xem đã có module nào vừa được thêm nhưng chưa save(chưa có estimation_id)
                ls_not_datas = module_db.search([('estimation_id', '=', False),\
                                                                    ('get_estimation_id', '=', record.get_estimation_id)
                                                                ])
                if ls_not_datas:
                    max_not_data = max(rec.sequence for rec in ls_not_datas)
                   
                max_sequence =  max(max_exist_data, max_not_data)
                record.sequence = max_sequence + 1
                # record.component = 'Module ' + str(record.sequence)
            record.update({
                'module_config_activity': activities_line,
                'module_effort_activity': activities_effort_line
                })
    
    def check_unique_components(ls_datas, record):
        count_db = 0
        for item in ls_datas:
            if record.component == item.component:
                count_db += 1
        return count_db
    
    @api.depends('module_config_activity.effort')
    def _compute_total_mandays(self):
        for record in self:
            total = sum( item.effort for item in record.module_config_activity)
            record.total_manday = total
    
    @api.depends('check_compute')
    def _compute_sequence(self):
        max = self.estimation_id.sequence_module
        for record in self:
            #if click load activities mode
            if record.get_estimation_id == 0:
                if record.estimation_id.id:
                    record.get_estimation_id = record.estimation_id.id
                #if edit mode
                elif record.estimation_id.id.origin:
                    record.get_estimation_id =record.estimation_id.id.origin
                else:
                    record.get_estimation_id = 999999
            record.sequence = max
            # record.component = 'Module ' + str(max)
            if record.id or record.id.origin == False :
                max += 1

    @api.onchange('component')
    def _compute_components(self):
        count = 0
        for record in self:
            for rec in self.estimation_id.add_lines_module:
                if record.component == rec.component:
                    count += 1
            if count > 1:
                record.component = False
                return {
                    'warning': {
                        'title': 'Warning!',
                        'message': 'Module components already exists!'
                    }
                } 

    @api.depends('module_config_activity')
    def _compute_sequence_activities(self):
        model = 'config.activity'
        sequence_field = 'sequence_activities'
        ls_data_fields = 'module_config_activity'
        for record in self:
            domain = [('module_id', '=', record.id or record.id.origin)]
            self.env['estimation.work']._compute_sequence_all(record, model, domain, sequence_field, ls_data_fields)
            
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
                    breakdown.mandays = round((breakdown.percent_effort * effort_activity_current)/ 100, 2)
      
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
                    if rec.activity == item.activity:
                        check_exist_in_self = True
                for act in ls_data_effort_activity:
                    if rec.activity == act.activity:
                        check_exist_in_data = True
                if check_exist_in_self == False and check_exist_in_data == False:
                    EstimationModule._get_activities(rec, record)
                
            # Case: delete record
            EstimationModule._delete_activities(record.module_effort_activity, record.module_config_activity)
            
    def _get_activities(ls_config_activities, record):
        line = []
        for rec in ls_config_activities:
            effort_line = (0, 0, {
                    'sequence': rec.sequence,
                    'activity': rec.activity,
                    'effort': rec.effort,
                    'module_id': record.id or record.id.origin,
            })
            line.append(effort_line)
        record.update({
            'module_effort_activity': line
        })

    def _delete_activities(ls_effort_activity, ls_config_activities):
        for record in ls_effort_activity:
            if record.activity not in [rec.activity for rec in ls_config_activities]:
                record.write({'module_id': [(2, record.module_id.id or record.module_id.id.origin)]})
                

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
    mandays = fields.Float(string="Expected (man-days)", readonly=True, default=0, store=True, compute='_compute_mandays')
    persons = fields.Integer(string="Persons", default=0)
    days = fields.Float(string="Days", default=0)
    percent_effort = fields.Float(string="Percent Effort (%)", default=0.0)
    type = fields.Selection(string="Type", store=True, related='activity_id.activity_type')
    
    check_compute = fields.Char(string="Check", readonly=True)

    @api.model
    def default_get(self, fields):
        result = super(BreakdownActivities, self).default_get(fields)
        result.update({'check_compute': 'OK'})
        return result

    @api.depends('activity_id.activity_type', 'activity_id.activity_current', 'persons', 'days', 'percent_effort')
    def _compute_mandays(self):
        for record in self:
            if record.activity == False:
                record.activity = 'Activity ' + str(record.sequence)
            if len(record.job_pos) == 0:
                job_pos_id = self.env['config.job.position'].search([], limit=1)
                record.job_pos = job_pos_id.id
            if record.type == 'type_3':
                record.mandays = record.persons * record.days
            elif record.type == 'type_1':
                if record.activity_id.activity_current:
                    #because only the parent element can get the changed value of the child element => get value effort of activity_curent from module parent
                    effort_activity_current = BreakdownActivities._find_effort_activity_current(record.activity_id.module_id.module_config_activity, record.activity_id.activity_current)
                    record.mandays = round((record.percent_effort * effort_activity_current)/ 100, 2)
                else:
                    record.mandays = 0
                    
    def _find_effort_activity_current(ls_activity, activity_current):
        result_effort = 0
        for record in ls_activity:
            if record.activity == activity_current.activity:
                result_effort = record.effort
        return result_effort

    @api.depends('check_compute')
    def _compute_sequence(self):
        for record in self.activity_id:
            # if save module mode
            if record.id or record.id.origin:
                max = record.sequence_breakdown
                for rec in self:
                   if rec.activity_id.id == record.id:
                        rec.sequence = max
                        max += 1
            else: #if this is create new activity
                max = record.sequence_breakdown
                for rec in self:
                    rec.sequence = max
                    if rec.id or rec.id.origin == False:
                        max += 1
                        
class EffortActivities(models.Model):
    _name = "module.effort.activity"
    _description = "Module effort distribute activity"
    _rec_name = "activity"
    _order = "sequence,id"
    
    module_id = fields.Many2one("estimation.module", string="Module")
    # activity_id = fields.Many2one('config.activity', string="Activities Work Breakdown")
    
    sequence = fields.Integer(string="No", index=True, store=True)
    activity = fields.Char(string="Activity")
    effort = fields.Float(string='Effort', compute='_compute_effort', store=True)
    percent = fields.Float(string="Percentage (%)", default=0, store=True, compute='_compute_percentage')
    
    # compute_effort is required for the _compute_percentage method to work correctly
    @api.depends('module_id.module_config_activity.effort', 'module_id.module_config_activity.activity')
    def _compute_effort(self):
        for record in self:
            for rec in record.module_id.module_config_activity:
                if record.activity == rec.activity:
                    record.effort = rec.effort
                    record.activity = rec.activity
            
    @api.depends('effort', 'module_id.module_config_activity')
    def _compute_percentage(self):
        #if delete config activities record (because module_effort_activity didn't load in time after deleting an config_activity) => get effort from module_config_activity
        total_effort = sum(rec.effort for rec in self.module_id.module_config_activity)
        for rec in self:
            if total_effort != 0.0:
                rec.percent = round((rec.effort / total_effort ) * 100, 2)
            else:
                rec.percent = total_effort