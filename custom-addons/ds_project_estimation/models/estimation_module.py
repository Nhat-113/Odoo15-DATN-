from odoo import models, fields, api

class EstimationModule(models.Model):
    _name = "estimation.module"
    _description ="Estimation List Modules"
    _rec_name = "component"
    _order = "sequence,id"
    
    sequence = fields.Integer(string="No", index=True, readonly=True, store=True, compute='_compute_components')
    component = fields.Char(string="Components", readonly=True, store=True, compute='_compute_components')
    total_manday = fields.Float(string="Total (man-day)", default=0.0, store=True, compute="_compute_total_mandays") 
    check_compute = fields.Char(string="Check", compute='_compute_check', store=True, readonly=True)
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    module_assumptions = fields.One2many('estimation.module.assumption', 'module_id')
    module_summarys = fields.One2many('estimation.module.summary', 'module_id')
    module_config_activity = fields.One2many('config.activity', 'module_id')
    module_effort_activity = fields.One2many('module.effort.activity', 'module_id')
    estimation_resource_plan = fields.One2many('estimation.resource.effort', 'module_id')
    
    @api.model
    def create(self, vals):
        if vals:
            result = super(EstimationModule, self).create(vals)
            vals_resource_plan = {'module_id': result.id, 
                                  'estimation_id': result.estimation_id.id, 
                                  'sequence': result.sequence, 
                                  'name': result.component }
            self.env['estimation.resource.effort'].create(vals_resource_plan)
            ls_resource_efforts = self.env['estimation.resource.effort'].search([('estimation_id', '=', result.estimation_id.id)])
            check = False
            for record in ls_resource_efforts:
                if record.name == 'Total (MD)' or record.name == 'Total (MM)':
                    check = True
            if check == False:
                vals_md_mm = {
                    'estimation_id': result.estimation_id.id,
                    'sequence': 2,
                    'name': 'Total (MD)',
                    'design_effort': 0,
                    'dev_effort': 0,
                    'tester_effort': 0,
                    'comtor_effort': 0,
                    'brse_effort': 0,
                    'pm_effort': 0,
                    'total_effort': 0,
                }
                self.env['estimation.resource.effort'].create(vals_md_mm)
                
                vals_md_mm['name'] = 'Total (MM)'
                vals_md_mm['sequence'] = 3
                self.env['estimation.resource.effort'].create(vals_md_mm)
            return result 
    
    def unlink(self):
        for record in self:
            record.module_assumptions.unlink()
            record.module_summarys.unlink()
            record.module_effort_activity.unlink()
            record.module_config_activity.unlink()
            
            check_data_resource_plan = self.env['estimation.resource.effort'].search([('estimation_id', '=', record.estimation_id.id)])
            gantt_resource_plan = self.env['gantt.resource.planning'].search([('estimation_id', '=', record.estimation_id.id)])
            if check_data_resource_plan:
                count = 0
                for rec in check_data_resource_plan:
                    count +=1
                if count == 3:  # there is 1 module and 2 record mm + md -> delete all record
                    check_data_resource_plan.unlink()  # delete all record
                    
                    if gantt_resource_plan:  # remove gantt
                        gantt_resource_plan.unlink()
                elif count > 3: # there are many modules -> delete 1 record
                    for item in check_data_resource_plan:
                        if item.module_id.id == record.id:
                            item.unlink()
        return super(EstimationModule, self).unlink()
                
    @api.model
    def default_get(self, fields):
        res = super(EstimationModule, self).default_get(fields)
        get_data_activities = self.env['data.activity'].search([])
        data_summary = self.env['data.module.summary'].search([])
        summary_line = []
        activities_line = []
        activities_effort_line = []
        
        for item in data_summary:
            line = (0, 0, {
                'summary_type': item.summary_type,
                'description' : item.description,
                'value': item.value,
                'type': item.type
            })
            summary_line.append(line)
        
        for record in get_data_activities:
            content = {
                'sequence': record.sequence, 
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
        
        res.update({
            'module_summarys': summary_line,
            'module_effort_activity': activities_effort_line,
            'module_config_activity': activities_line,
            'check_compute': 'Y'  #is required for compute sequence
        })
        return res
  
    @api.depends('module_config_activity.effort')
    def _compute_total_mandays(self):
        for record in self:
            total = 0.0
            for item in record.module_config_activity:
                total += item.effort
            record.total_manday = total
    
    @api.depends('check_compute')
    def _compute_components(self):
        max = 0
        for record in self:
            max = record.estimation_id.sequence_module
            break
        for record in self:
            record.sequence = max
            record.component = 'Module ' + str(max)
            if record.id or record.id.origin == False :
                max += 1

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
    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence') #compute='_compute_sequence', 
    activity = fields.Char("Activity", required=True)
    job_pos = fields.Many2one('config.job.position', string="Job Position", required=True)
    mandays = fields.Float(string="Expected (man-days)", readonly=True, default=0, store=True, compute='_compute_mandays')
    persons = fields.Integer(string="Persons", default=0)
    days = fields.Float(string="Days", default=0)
    percent_effort = fields.Float(string="Percent Effort (%)", default=0.0)
    type = fields.Selection(string="Type", store=True, related='activity_id.activity_type')

    @api.model
    def create(self, vals):
        if vals:
            ls_breakdown = self.env['module.breakdown.activity'].search([('activity_id', '=', vals['activity_id'])])
            self.env['config.activity'].auto_increase_sequence(vals, ls_breakdown)
            return super(BreakdownActivities, self).create(vals)

    @api.depends('activity_id.activity_type', 'activity_id.activity_current', 'persons', 'days', 'percent_effort', 'sequence')
    def _compute_mandays(self):
        for record in self:
            if record.type == 'type_3':
                record.mandays = record.persons * record.days
            elif record.type == 'type_1':
                if record.activity_id.activity_current:
                    record.mandays = round((record.percent_effort * record.activity_id.activity_current.effort)/ 100, 2)
                else:
                    record.mandays = 0

class EffortActivities(models.Model):
    _name = "module.effort.activity"
    _description = "Module effort distribute activity"
    _rec_name = "activity"
    _order = "sequence,id"
    
    module_id = fields.Many2one("estimation.module", string="Module")
    activity_id = fields.Many2one('config.activity', string="Activities Work Breakdown")
    
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity = fields.Char(string="Activity")
    effort = fields.Float(string='Effort', compute='_compute_effort', store=True)
    percent = fields.Float(string="Percentage (%)", default=0, store=True, compute='_compute_percentage')
    
    # compute_effort is required for the _compute_percentage method to work correctly
    @api.depends('activity_id.effort', 'module_id.total_manday', 'activity_id')
    def _compute_effort(self):
        for rec in self:
            rec.effort = rec.activity_id.effort
            
    @api.depends('effort', 'activity_id')
    def _compute_percentage(self):
        rs_module_id = 0
        check_module_id = True
        for record in self:
            if record.module_id.id:
                rs_module_id = record.module_id.id
                break
            elif record.module_id.id == False:
                check_module_id = False
                break
            elif record.module_id.id.origin:
                rs_module_id = record.module_id.id.origin
                break
            else:
                check_module_id = False
                break
            
        if check_module_id:
            ls_effort_distribute = self.env['module.effort.activity'].search([('module_id', '=', rs_module_id)])
            total_effort = 0.0
            for record in ls_effort_distribute:
                total_effort += record.effort
            for record in ls_effort_distribute:
                if total_effort != 0.0:
                    record.percent = round((record.effort / total_effort ) * 100, 2 )
                else:
                    record.percent = total_effort
    
    @api.model
    def create(self, vals):
        if vals:
            if 'activity_id' in vals:
                return super(EffortActivities, self).create(vals)
            activity_id = self.env['config.activity'].search([('module_id', '=', vals['module_id']), ('sequence', '=', vals['sequence'])])
            vals['activity_id'] = activity_id.id
            return super(EffortActivities, self).create(vals)
