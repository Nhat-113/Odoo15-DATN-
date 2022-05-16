from odoo import models, fields, api

class EstimationModuleAssumption(models.Model):
    _name = "estimation.module.assumption"
    _description = "Module Assumption of each estimation"

    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    assumption = fields.Text("Assumption")


class EstimationModuleSummary(models.Model):
    _name = "estimation.module.summary"
    _description = "Module Summary of each estimation"
    
    name = fields.Char(string="Name")
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    connect_module = fields.Many2one('estimation.work', string="Connect Module")
    summary_type = fields.Char(string="Summary Type")
    time_effort_value = fields.Float(string="Value",)
    working_efforts = fields.Char(string="Working Time/Efforts")

   
class BreakdownActivities(models.Model):
    """
    Describe breakdown activities
    """
    _name = "module.breakdown.activity"
    _description = "Module Breakdown of each activity"
    _order = "sequence,id"

    activity_id = fields.Many2one('config.activity', string="Connect Activity Module")
    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity", required=True)
    job_pos = fields.Many2one('config.job_position', string="Job Position")
    mandays = fields.Float(string="Expected (man-days)", default=0)
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

class EffortActivities(models.Model):
    _name = "module.effort.activity"
    _description = "Module effort distribute activity"
    _rec_name = "activity"
    
    estimation_id = fields.Many2one('estimation.work', string="Estimation")
    activity_id = fields.Many2one('config.activity', string="Connect Module")
    
    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity", readonly=True, store=True, compute='_compute_activity')
    effort = fields.Float(string="Effort", default=0, readonly=True, store=True, compute='_compute_total_effort')
    percent = fields.Float(string="Percentage", default=0, readonly=True, store=True, compute='_compute_percentage')

    
    @api.depends('activity_id.effort')
    def _compute_total_effort(self):
        for rec in self:
            rec.effort = rec.activity_id.effort
            
    @api.depends('effort')
    def _compute_percentage(self):
        ls_effort_distribute = self.env['module.effort.activity'].search([('estimation_id', '=', self.estimation_id.ids[0])]) #self.env.context['params']['id']
        total_effort = 0.0        
        for record in ls_effort_distribute:
            total_effort += record.effort
        for record in ls_effort_distribute:
            if total_effort != 0.0:
                record.percent = round((record.effort / total_effort ) * 100, 2 )
            else:
                record.percent = total_effort
                
    @api.depends('activity_id.activity')
    def _compute_activity(self):
        for rec in self:
            rec.activity = rec.activity_id.activity

