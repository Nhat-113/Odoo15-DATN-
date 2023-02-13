from odoo import models, fields, api
import math
from datetime import datetime, timedelta

Index_year = 0  #This is for compute_year function
class EstimationResourcePlan(models.Model):
    _name = "estimation.resource.effort"
    _description = "Resource planning of each estimation"
    _order = "sequence"
    
    estimation_id = fields.Many2one('estimation.work', string="Connect Estimation")
    sequence = fields.Integer(string="No", store=True)
    name= fields.Char(string="Components")
    key_primary = fields.Char(string="Key unique module")
    total_effort = fields.Float(string="Total Effort (MD)", store=True, compute="compute_effort") 


    def total_efforts_job_position(self, job_position):
        result_total_effort = 0
        for record in self.estimation_id.add_lines_module:
            if record.key_primary == self.key_primary:
                for activity in record.module_config_activity:
                    for breakdown in activity.add_lines_breakdown_activity: # compute effort for each job position
                        if breakdown.job_pos.job_position == job_position:
                            result_total_effort += breakdown.mandays
        return result_total_effort
    
    @api.depends('estimation_id.add_lines_module.total_manday')
    def compute_effort(self):
        ls_key = self.env['estimation.summary.totalcost'].get_field_effort({})
        for key in ls_key:
            final_effort = final_total_effort = 0
            for record in self:     # compute total effort for each module
                if record.name not in ['Total (MD)', 'Total (MM)']:
                    result_total_efforts = EstimationResourcePlan.total_efforts_job_position(record, ls_key[key])
                    record[key] = result_total_efforts
                    final_effort += result_total_efforts
                    
                    #get total manday from module = total_effort field
                    for module in record.estimation_id.add_lines_module:
                        if module.key_primary == record.key_primary:
                            record.total_effort = module.total_manday
                            final_total_effort += module.total_manday
            #compute effort for MD & MM record
            for record in self.estimation_id.resource_plan_result_effort: 
                if record.name == 'Total (MD)':
                    record[key] = final_effort
                    record.total_effort = final_total_effort
                elif record.name =='Total (MM)':
                    man_month = 20  # 20 is working days per month
                    if man_month != 0:
                        record[key] = round (final_effort / man_month, 2)
                        record.total_effort = round (final_total_effort / man_month, 2)
                    
class EstimationResourcePlanResultEffort(models.Model):
    _name = 'estimation.resource.plan.result.effort'
    _description = 'Model is saving total effort MM & MD for estimation resource plan'
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    sequence = fields.Integer(string="No", store=True)
    name = fields.Char(string="Component")
    total_effort = fields.Float(string="Total Effort (MD)")
    key_primary = fields.Char(string="Key unique")
    
    
    @api.model
    def create(self, vals):
        if vals:
            result = super(EstimationResourcePlanResultEffort, self).create(vals)
            if vals['key_primary'] == 'totalmm':
                ls_key = self.env['estimation.summary.totalcost'].get_field_effort({})
                self.check_missing_field_values(vals, ls_key)
                for key in vals:
                    for item in ls_key:
                        if key == item:
                            yy_start =  int(str(result.create_date.year)[-2:])  #take the last 2 numbers of the year
                            mm_start =  result.create_date.month
                            result_day = EstimationResourcePlanResultEffort.compute_date_time(vals[key], mm_start, yy_start)
                            vals_gantt = {
                                'estimation_id': vals['estimation_id'],
                                'job_position_id': EstimationResourcePlanResultEffort.find_job_position(self, ls_key[item]),
                                'value_man_month': vals[key],
                                'start_date': result_day['start_date'],
                                'duration': (result_day['end_date'] - result_day['start_date']).days + 1
                            }
                            
                            self.env["gantt.resource.planning"].create(vals_gantt)
            return result
        
        
    def check_missing_field_values(self, vals, ls_keys):
        for key in ls_keys:
            if key not in vals:
                vals.update({key: 0})
    
    
    def write(self, vals):
        if vals:
            result = super(EstimationResourcePlanResultEffort, self).write(vals)
            ls_key = self.env['estimation.summary.totalcost'].get_field_effort({})
            vals_gantt= {}
            for rec in self:
                if rec.key_primary == 'totalmm':
                    for key in vals:
                        for item in ls_key:
                            if key == item:
                                job_pos_id = EstimationResourcePlanResultEffort.find_job_position(self, ls_key[item])
                                gantt_item = self.env['gantt.resource.planning'].search([('estimation_id', '=', rec.estimation_id.id), 
                                                                                       ('job_position_id', '=', job_pos_id)])
                                for i in vals:
                                    vals_gantt['value_man_month'] = vals[i]
                                    
                                yy_start =  int(str(rec.create_date.year)[-2:])   #take the last 2 numbers of the year
                                mm_start =  rec.create_date.month
                                result_day = EstimationResourcePlanResultEffort.compute_date_time(vals_gantt['value_man_month'], mm_start, yy_start)
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
        
        if vals_effort_mm < 0:
            mm_end = mm_start 
            # scale = 1/31
            surplus = 0 
            dd_end = 1
            result_end_day = EstimationResourcePlanResultEffort.convert_to_datetime(dd_end, mm_end, yy_end)
        
        elif vals_effort_mm < 1:
            mm_end = mm_start 
            # scale = 1/31
            surplus = vals_effort_mm 
            if surplus == 0:
                dd_end = 1
            else:
                dd_end = EstimationResourcePlanResultEffort.compute_days(mm_end, surplus, dd_end)
            if dd_end == 0:
                dd_end = 1
            # yy_end = yy_start
            result_end_day = EstimationResourcePlanResultEffort.convert_to_datetime(dd_end, mm_end, yy_end)
        elif vals_effort_mm >= 1:
            if mm_start + vals_effort_mm < 13:
                mm_end = math.floor(mm_start + vals_effort_mm)
                surplus = (mm_start + vals_effort_mm) - mm_end
                if mm_end == 12:
                    mm_end = 1
                    yy_end = yy_start + 1

                result_dd_end = EstimationResourcePlanResultEffort.compute_days(mm_end, surplus, dd_end)
                if result_dd_end == 0:
                    dd_end = 1
                else:
                    dd_end = result_dd_end
                result_end_day = EstimationResourcePlanResultEffort.convert_to_datetime(dd_end, mm_end, yy_end)
            elif mm_start + vals_effort_mm >= 13:
                datetime_end = EstimationResourcePlanResultEffort.compute_year(vals_effort_mm, mm_start, yy_start, dd_end, mm_end, yy_end)
                global Index_year
                Index_year = 0
                for item in datetime_end:
                    if item == 'dd_end':
                        dd_end = datetime_end[item]
                    elif item == 'mm_end':
                        mm_end = datetime_end[item]
                    else:
                        yy_end = datetime_end[item]
                result_end_day = EstimationResourcePlanResultEffort.convert_to_datetime(dd_end, mm_end, yy_end)
        result_start_day = EstimationResourcePlanResultEffort.convert_to_datetime(dd_start, mm_start, yy_start)
        return {
            'start_date': result_start_day, 
            'end_date': result_end_day
        }
        
    def compute_year(vals_effort_mm, mm_start, yy_start, dd_end, mm_end, yy_end):
        global Index_year
        check_vals = (mm_start + vals_effort_mm) - 12        #12 is 12 month/year
        if check_vals > 12:
            Index_year += 1
            return EstimationResourcePlanResultEffort.compute_year(check_vals, mm_start, yy_start, dd_end, mm_end, yy_end)
        elif check_vals <= 12:
            mm_end = math.floor(check_vals)
            surplus = check_vals - mm_end
            if mm_end == 12:
                mm_end = 1
                yy_end = yy_start + Index_year + 1
            else:
                yy_end = yy_start + Index_year
            dd_end = EstimationResourcePlanResultEffort.compute_days(mm_end, surplus, dd_end)
            if dd_end == 0:
                dd_end = 1
        return {'dd_end': dd_end, 'mm_end': mm_end, 'yy_end': yy_end}
        
    def compute_days(mm_end, surplus, dd_end):
        if mm_end == 2:   #2 is february
            scale = 1/28   # 1 is max scale surplus
            dd_end = round(surplus / scale)
        elif EstimationResourcePlanResultEffort.find_month(mm_end):
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
