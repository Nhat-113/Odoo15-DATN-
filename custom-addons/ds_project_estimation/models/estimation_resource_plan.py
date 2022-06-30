from odoo import models, fields, api
import math
from datetime import datetime, timedelta

Index_year = 0  #This is for compute_year function
class EstimationResourcePlan(models.Model):
    _name = "estimation.resource.effort"
    _description = "Resource planning of each estimation"
    _order = "sequence"
    
    estimation_id = fields.Many2one('estimation.work', string="Connect Estimation")
    # module_id = fields.Many2one("estimation.module", string="Module")
    sequence = fields.Integer(string="No", store=True, compute='compute_sequence')
    name= fields.Char(string="Components")
    temp_field = fields.Float(string="temp", store=True, compute="compute_effort")
    design_effort = fields.Float(string="Designer")
    dev_effort = fields.Float(string="Developer")
    tester_effort = fields.Float(string="Tester")
    comtor_effort = fields.Float(string="Comtor")
    brse_effort = fields.Float(string="Brse")
    pm_effort = fields.Float(string="PM")
    total_effort = fields.Float(string="Total Effort (MD)", store=True, compute="compute_effort") 
   
   
    def total_efforts_job_position(self, job_position):
        result_total_effort = 0
        for record in self.estimation_id.add_lines_module:
            if record.component == self.name:
                for activity in record.module_config_activity:
                    for breakdown in activity.add_lines_breakdown_activity: # compute effort for each job position
                        if breakdown.job_pos.job_position == job_position:
                            #if this is save mode
                            if breakdown.id:
                                result_total_effort += breakdown.mandays
                            else:
                                #compute breakdown is new
                                result_total_effort += breakdown.mandays
                                
                                #compute effort from database because self has no effort data
                                ls_breakdowns = self.env['module.breakdown.activity'].search([('activity_id', '=', activity.id or activity.id.origin), ('job_pos', '=', breakdown.job_pos.id)])
                                total = sum(breakdb.mandays for breakdb in ls_breakdowns)
                                result_total_effort += total
        return result_total_effort
    
    @api.depends('estimation_id.add_lines_module.total_manday')
    def compute_effort(self):
        ls_key = {'dev_effort': 'Developer', 'design_effort': 'Designer', 'tester_effort': 'Tester', 
                  'comtor_effort': 'Comtor', 'pm_effort': 'Project manager', 'brse_effort': 'Brse'}
        for key in ls_key:
            final_effort = final_total_effort = 0
            for record in self:     # compute total effort for each module
                if record.name not in ['Total (MD)', 'Total (MM)']:
                    result_total_efforts = EstimationResourcePlan.total_efforts_job_position(record, ls_key[key])
                    record[key] = result_total_efforts
                    final_effort += result_total_efforts
                    
                    #get total manday from module = total_effort field
                    for module in record.estimation_id.add_lines_module:
                        if module.component == record.name:
                            record.total_effort = module.total_manday
                            final_total_effort += module.total_manday
            #compute effort for MD & MM record
            for record in self: 
                if record.name == 'Total (MD)':
                    record[key] = final_effort
                    record.total_effort = final_total_effort
                elif record.name =='Total (MM)':
                    man_month = 20  # 20 is working days per month
                    if man_month != 0:
                        record[key] = round (final_effort / man_month, 2)
                        record.total_effort = round (final_total_effort / man_month, 2)
                    
    @api.model
    def create(self, vals):
        if vals:
            result = super(EstimationResourcePlan, self).create(vals)
            record_sum_effort = 'Total (MM)'
            
            ls_key = {'design_effort': 'Designer', 'dev_effort': 'Developer', 'tester_effort': 'Tester', 
                      'comtor_effort': 'Comtor', 'brse_effort': 'Brse', 'pm_effort': 'Project manager'}
            
            vals_gantt = {}
            vals_gantt['estimation_id'] = vals['estimation_id']
            if vals['name'] == record_sum_effort:
                for key in vals:
                    for item in ls_key:
                        if key == item:
                            vals_gantt['job_position_id'] = EstimationResourcePlan.find_job_position(self, ls_key[item])
                            vals_gantt['value_man_month'] = vals[key]
                            yy_start =  int(str(result.create_date.year)[-2:])  #take the last 2 numbers of the year
                            mm_start =  result.create_date.month
                            result_day = EstimationResourcePlan.compute_date_time(vals[key], mm_start, yy_start)
                            vals_gantt['end_date'] = result_day['end_date']
                            vals_gantt['start_date'] = result_day['start_date']
                            vals_gantt['duration'] = (vals_gantt['end_date'] - vals_gantt['start_date']).days + 1
                            vals_gantt.pop("end_date")
                            self.env["gantt.resource.planning"].create(vals_gantt)
            
            return result       
        
    def write(self, vals):
        if vals:
            result = super(EstimationResourcePlan, self).write(vals)
            ls_key = {'design_effort': 'Designer', 'dev_effort': 'Developer', 'tester_effort': 'Tester', 
                      'comtor_effort': 'Comtor', 'brse_effort': 'Brse', 'pm_effort': 'Project manager'}
            vals_gantt= {}
            for rec in self:
                if rec.name == 'Total (MM)':
                    for key in vals:
                        for item in ls_key:
                            if key == item:
                                job_pos_id = EstimationResourcePlan.find_job_position(self, ls_key[item])
                                gantt_item = self.env['gantt.resource.planning'].search([('estimation_id', '=', rec.estimation_id.id), 
                                                                                       ('job_position_id', '=', job_pos_id)])
                                for i in vals:
                                    vals_gantt['value_man_month'] = vals[i]
                                    
                                yy_start =  int(str(rec.create_date.year)[-2:])   #take the last 2 numbers of the year
                                mm_start =  rec.create_date.month
                                result_day = EstimationResourcePlan.compute_date_time(vals_gantt['value_man_month'], mm_start, yy_start)
                                vals_gantt['duration'] = (result_day['end_date'] - result_day['start_date']).days + 1
                                GanttResourcePlanning.write(gantt_item, vals_gantt)
                                break
                    
            return result
    
    def find_job_position(self, var):
        ls_job_position = self.env['config.job.position']. search([])
        for item in ls_job_position:
            if item.job_position == var:
                return item.id
            
    def compute_date_time(vals_effort_mm, mm_start, yy_start):
        dd_start = dd_end = 1
        mm_end = mm_start
        yy_end = yy_start
        surplus = 0
        if vals_effort_mm < 1:
            mm_end = mm_start 
            # scale = 1/31
            surplus = vals_effort_mm 
            if surplus == 0:
                dd_end = 1
            else:
                dd_end = EstimationResourcePlan.compute_days(mm_end, surplus, dd_end)
            if dd_end == 0:
                dd_end = 1
            # yy_end = yy_start
            result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
        elif vals_effort_mm >= 1:
            if mm_start + vals_effort_mm < 13:
                mm_end = math.floor(mm_start + vals_effort_mm)
                surplus = (mm_start + vals_effort_mm) - mm_end
                if mm_end == 12:
                    mm_end = 1
                    yy_end = yy_start + 1

                result_dd_end = EstimationResourcePlan.compute_days(mm_end, surplus, dd_end)
                if result_dd_end == 0:
                    dd_end = 1
                else:
                    dd_end = result_dd_end
                result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
            elif mm_start + vals_effort_mm >= 13:
                datetime_end = EstimationResourcePlan.compute_year(vals_effort_mm, mm_start, yy_start, dd_end, mm_end, yy_end)
                global Index_year
                Index_year = 0
                for item in datetime_end:
                    if item == 'dd_end':
                        dd_end = datetime_end[item]
                    elif item == 'mm_end':
                        mm_end = datetime_end[item]
                    else:
                        yy_end = datetime_end[item]
                result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
        result_start_day = EstimationResourcePlan.convert_to_datetime(dd_start, mm_start, yy_start)
        return {
            'start_date': result_start_day, 
            'end_date': result_end_day
        }
        
    def compute_year(vals_effort_mm, mm_start, yy_start, dd_end, mm_end, yy_end):
        global Index_year
        check_vals = (mm_start + vals_effort_mm) - 12        #12 is 12 month/year
        if check_vals > 12:
            Index_year += 1
            return EstimationResourcePlan.compute_year(check_vals, mm_start, yy_start, dd_end, mm_end, yy_end)
        elif check_vals <= 12:
            mm_end = math.floor(check_vals)
            surplus = check_vals - mm_end
            if mm_end == 12:
                mm_end = 1
                yy_end = yy_start + Index_year + 1
            else:
                yy_end = yy_start + Index_year
            dd_end = EstimationResourcePlan.compute_days(mm_end, surplus, dd_end)
            if dd_end == 0:
                dd_end = 1
        return {'dd_end': dd_end, 'mm_end': mm_end, 'yy_end': yy_end}
        
    def compute_days(mm_end, surplus, dd_end):
        if mm_end == 2:   #2 is february
            scale = 1/28   # 1 is max scale surplus
            dd_end = round(surplus / scale)
        elif EstimationResourcePlan.find_month(mm_end):
            scale = 1/30
            dd_end = round(surplus / scale)
        else:
            scale = 1/31
            dd_end = round(surplus / scale)
        return dd_end

    def find_month(mm_end):
        month_30_day = [4, 6, 9, 11]
        check = False
        for item in month_30_day:
            if item == mm_end:
                check = True
        return check  
    
    def convert_to_datetime(dd, mm, yy):
        date_string = str(dd) + '/' + str(mm) + '/' + str(yy)
        return datetime.strptime(date_string, '%d/%m/%y').date()
    
    @api.depends('estimation_id.sequence_module')
    def compute_sequence(self):
        max_sequence = 0
        for record in self:
            if record.name not in ['Total (MD)', 'Total (MM)']:
                if record.id:
                    max_sequence += 1
                    record.sequence = max_sequence 
                elif record.sequence > max_sequence:
                    # elif record.id.origin and record.sequence > max_sequence:
                    max_sequence = record.sequence
               
        for record in self:
            if record.name == 'Total (MD)':
                record.sequence = max_sequence + 1
            elif record.name == 'Total (MM)':
                record.sequence = max_sequence + 2

    def unlink(self):
        for record in self:
            if record.name == 'Total (MM)':
                gantt_resource_plan = self.env['gantt.resource.planning'].search([('estimation_id', '=', record.estimation_id.id)])
                gantt_resource_plan.unlink()

        return super(EstimationResourcePlan, self).unlink()

class GanttResourcePlanning(models.Model):
    _name = "gantt.resource.planning"
    _description = "Gantt resource planning"
    _order = "id"
    estimation_id = fields.Many2one('estimation.work')
    job_position_id = fields.Many2one('config.job.position')
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    value_man_month = fields.Float(string="Total (MM)")
    progress = fields.Integer(string="Progress", default= 100)
    duration = fields.Integer(string="Duration", store=True, compute='_compute_check_duration')
    
    @api.depends('duration', 'start_date', 'end_date')
    def _compute_check_duration(self):
        for rec in self:
            if rec.duration <= 0:
                rec.duration = 7   # 7 is 1 week
            else:
                rec.start_date += timedelta(days=1)