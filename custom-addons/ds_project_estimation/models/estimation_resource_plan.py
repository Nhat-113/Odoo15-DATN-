from odoo import models, fields, api
import math
from datetime import datetime

class EstimationResourcePlan(models.Model):
    _name = "estimation.resource.effort"
    _description = "Resource planning of each estimation"
    _order = "sequence,id"
    
    estimation_id = fields.Many2one('estimation.work', string="Connect Estimation")
    sequence = fields.Integer(string="No", )
    name= fields.Char(string="Components", default="Module")    
    design_effort = fields.Float(string="Design",)
    dev_effort = fields.Float(string="Dev",)
    tester_effort = fields.Float(string="Tester",)
    comtor_effort = fields.Float(string="Comtor",)
    brse_effort = fields.Float(string="Brse",)
    pm_effort = fields.Float(string="PM",)
    total_effort = fields.Float(string="Total Effort (MD)", store=True, compute="compute_effort")
    
    
    @api.depends('estimation_id.total_manday')
    def compute_effort(self):
        result_total_effort_des = EstimationResourcePlan.total_efforts_func(self, 'Designer')
        result_total_effort_dev = EstimationResourcePlan.total_efforts_func(self, 'Developer')
        result_total_effort_tes = EstimationResourcePlan.total_efforts_func(self, 'Tester')
        result_total_effort_com = EstimationResourcePlan.total_efforts_func(self, 'Comtor')
        result_total_effort_pm = EstimationResourcePlan.total_efforts_func(self, 'Project manager')
        result_total_effort_brs = EstimationResourcePlan.total_efforts_func(self, 'Brse')
        final_des_md = final_dev_md = final_tes_md = final_com_md = final_pm_md = final_brs_md = final_total_effort_md = 0.0
        module_name = "Module"
        for record in self:
            if record.name.find(module_name) != -1:
                record.design_effort = result_total_effort_des
                final_des_md += result_total_effort_des
                
                record.dev_effort = result_total_effort_dev
                final_dev_md += result_total_effort_dev
                
                record.tester_effort = result_total_effort_tes
                final_tes_md += result_total_effort_tes
                
                record.comtor_effort = result_total_effort_com
                final_com_md += result_total_effort_com
                
                record.pm_effort = result_total_effort_pm
                final_pm_md += result_total_effort_pm
                
                record.brse_effort = result_total_effort_brs
                final_brs_md += result_total_effort_brs
                
                record.total_effort = record.estimation_id.total_manday
                final_total_effort_md += record.total_effort
        for record in self: 
            if record.name == 'Total (MD)':
                record.design_effort = final_des_md
                record.dev_effort = final_dev_md
                record.tester_effort = final_tes_md
                record.comtor_effort = final_com_md
                record.pm_effort = final_pm_md
                record.brse_effort = final_brs_md
                record.total_effort = final_total_effort_md
                
            elif record.name == 'Total (MM)':
                # man_month = self.env['estimation.module.summary'].search([('estimation_id', '=', record.estimation_id.id), ('type', '=', 'default_per_month')])
                man_month = 20  # 20 is working days per month
                if man_month != 0:
                    record.design_effort = round (final_des_md / man_month, 2)
                    record.dev_effort = round (final_dev_md / man_month, 2)
                    record.tester_effort = round (final_tes_md / man_month, 2)
                    record.comtor_effort = round (final_com_md / man_month, 2)
                    record.pm_effort = round (final_pm_md / man_month, 2)
                    record.brse_effort = round (final_brs_md / man_month, 2)
                    record.total_effort = round (final_total_effort_md / man_month, 2)


    def total_efforts_func(self, vars):
        ls_activities = self.env['config.activity'].search([('estimation_id', '=', self.estimation_id.id)]).ids
        result_total_effort = 0
        for item in ls_activities:
            ls_breakdowns = self.env['module.breakdown.activity'].search([('activity_id', '=', item)])
            for rec in ls_breakdowns:
                if rec.job_pos and rec.job_pos.job_position == vars:
                    result_total_effort += rec.mandays
        return result_total_effort

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
                            result_day = EstimationResourcePlan.compute_date_time(vals[key], yy_start)
                            for days in result_day:
                                if days == 'start_date': 
                                    vals_gantt['start_date'] = result_day['start_date']
                                else:
                                    vals_gantt['end_date'] = result_day['end_date']
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
                                    
                                yy_start =  22  #take the last 2 numbers of the year
                                result_day = EstimationResourcePlan.compute_date_time(vals_gantt['value_man_month'], yy_start)
                                for days in result_day:
                                    if days == 'start_date': 
                                        vals_gantt['start_date'] = result_day['start_date']
                                    else:
                                        vals_gantt['end_date'] = result_day['end_date']
                                GanttResourcePlanning.write(gantt_item, vals_gantt)
                                break
                    
            return result
    
    def find_job_position(self, var):
        ls_job_position = self.env['config.job.position']. search([])
        for item in ls_job_position:
            if item.job_position == var:
                return item.id
        
    def compute_date_time(vals_effort_mm, yy_start):
       
        dd_start = mm_start = 1
        dd_end = mm_end = yy_end = 1
        surplus = 0
        if vals_effort_mm < 1:
            mm_end = 1 
            scale = 1/31
            surplus = vals_effort_mm 
            if surplus == 0:
                dd_end = 1
            else:
                dd_end = round(surplus / scale)
            yy_end = yy_start
            result_start_day = EstimationResourcePlan.convert_to_datetime(dd_start, mm_start, yy_start)
            result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
            
        elif vals_effort_mm >= 1 and vals_effort_mm < 13:
            mm_end = math.floor(vals_effort_mm)
           
            yy_end = yy_start
            surplus = vals_effort_mm - mm_end
            result_dd_end = EstimationResourcePlan.compute_days(mm_end, surplus, dd_end)
            if result_dd_end == 0:
                dd_end = 1
            else:
                dd_end = result_dd_end
            result_start_day = EstimationResourcePlan.convert_to_datetime(dd_start, mm_start, yy_start)
            result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
           
        elif vals_effort_mm >= 13:
            datetime_end = EstimationResourcePlan.compute_year(vals_effort_mm, mm_start, yy_start, dd_end, mm_end, yy_end)
            for item in datetime_end:
                if item == 'dd_end':
                    dd_end = datetime_end[item]
                elif item == 'mm_end':
                    mm_end = datetime_end[item]
                else:
                    yy_end = datetime_end[item]

            result_start_day = EstimationResourcePlan.convert_to_datetime(dd_start, mm_start, yy_start)
            result_end_day = EstimationResourcePlan.convert_to_datetime(dd_end, mm_end, yy_end)
        return {
            'start_date': result_start_day, 
            'end_date': result_end_day
        }
        
    def compute_year(vals_effort_mm, mm_end, yy_start, dd_end, yy_end):
        index = 1
        check_vals = vals_effort_mm - 12        #12 is 12 month/year
        if check_vals > 12:
            index += 1 
            EstimationResourcePlan.compute_year(check_vals, mm_end, yy_start, dd_end, yy_end)
        elif check_vals <= 12:
            mm_end = math.floor(check_vals)
            surplus = check_vals - mm_end
            yy_end = yy_start + index
            dd_end = EstimationResourcePlan.compute_days(mm_end, surplus, dd_end)
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
           

class GanttResourcePlanning(models.Model):
    _name = "gantt.resource.planning"
    _description = "Gantt resource planning"
    _order = "id"
    estimation_id = fields.Many2one('estimation.work')
    job_position_id = fields.Many2one('config.job.position')
    start_date = fields.Date(string="Start date")
    end_date = fields.Date(string="End date")
    value_man_month = fields.Float(string="MM")
    planned_duration = fields.Integer(string="Duration", default= 100)
    links_serialized_json = fields.Char(string="json", default="[]")


class EstimationResourcePlanningData(models.Model):
    _name = "estimation.resource.planning.data"
    _description = "Resource planning data default of each estimation"
    _order = "sequence,id"
     
    sequence = fields.Integer(string="No")
    name= fields.Char(string="Components")    
    design_effort = fields.Float(string="Design")
    dev_effort = fields.Float(string="Dev")
    tester_effort = fields.Float(string="Tester")
    comtor_effort = fields.Float(string="Comtor")
    brse_effort = fields.Float(string="Brse")
    pm_effort = fields.Float(string="PM")
    total_effort = fields.Float(string="Total Effort (MD)")
    