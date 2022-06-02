from odoo import models, fields, api


class EstimationModuleAssumption(models.Model):
    _name = "estimation.module.assumption"
    _description = "Module Assumption of each estimation"

    connect_module = fields.Many2one(
        'estimation.work', string="Connect Module")
    assumption = fields.Text("Assumption")

class EstimationModuleSummary(models.Model):
    _name = "estimation.module.summary"
    _description = "Module Summary of each estimation"

    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    summary_type = fields.Char(string="Summary Type")
    description = fields.Char(string="Working Time/Efforts")
    value = fields.Float(string="Value", store=True, compute='_compute_value')
    type = fields.Char(string="Type")

    
    @api.depends('estimation_id.total_manday')
    def _compute_value(self):
        man_day_val = 0.0
        day_per_month = 0
        for record in self:
            if record.type == 'man_day':
                record.value = record.estimation_id.total_manday
                man_day_val = record.estimation_id.total_manday
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

    activity_id = fields.Many2one(
        'config.activity', string="Connect Activity Module")
    sequence = fields.Integer(
        string="No", index=True, readonly=True, help='Use to arrange calculation sequence') #compute='_compute_sequence', 
    activity = fields.Char("Activity", required=True)
    job_pos = fields.Many2one('config.job.position',
                              string="Job Position", required=True)
    mandays = fields.Float(string="Expected (man-days)", readonly=True,
                           default=0, store=True, compute='_compute_mandays')
    persons = fields.Integer(string="Persons", default=0)
    days = fields.Float(string="Days", default=0)
    percent_effort = fields.Float(string="Percent Effort (%)", default=0.0)
    type = fields.Selection(string="Type", store=True,
                            related='activity_id.activity_type')

    @api.model
    def create(self, vals):
        if vals:
            ls_breakdown = self.env['module.breakdown.activity'].search(
                [('activity_id', '=', vals['activity_id'])])
            self.env['config.activity'].auto_increase_sequence(
                vals, ls_breakdown)
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
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    activity_id = fields.Many2one('config.activity', string="Activities Work Breakdown")
    
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity = fields.Char(string="Activity", related='activity_id.activity')
    effort = fields.Float(string='Effort', compute='_compute_effort', store=True)
    percent = fields.Float(string="Percentage (%)", default=0, store=True, compute='_compute_percentage')
    
    # compute_effort is required for the _compute_percentage method to work correctly
    @api.depends('activity_id.effort', 'estimation_id.total_manday', 'activity_id')
    def _compute_effort(self):
        for rec in self:
            rec.effort = rec.activity_id.effort
            
    @api.depends('effort', 'activity_id')
    def _compute_percentage(self):
        rs_estimation_id = 0
        check_estimation_id = True
        for record in self:
            if record.estimation_id.id:
                rs_estimation_id = record.estimation_id.id
                break
            elif record.estimation_id.id == False:
                check_estimation_id = False
                break
            elif record.estimation_id.id.origin:
                rs_estimation_id = record.estimation_id.id.origin
                break
            else:
                check_estimation_id = False
                break
            
        if check_estimation_id:
            ls_effort_distribute = self.env['module.effort.activity'].search([('estimation_id', '=', rs_estimation_id)])
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
            check = False
            for key in vals:
                if key == 'activity_id':
                    check = True
                    break
            if check == False:
                activity_id = self.env['config.activity'].search([('estimation_id', '=', vals['estimation_id']), ('sequence', '=', vals['sequence'] )])
                vals['activity_id'] = activity_id.id
                return super(EffortActivities, self).create(vals)
            else:
                return super(EffortActivities, self).create(vals)
                

