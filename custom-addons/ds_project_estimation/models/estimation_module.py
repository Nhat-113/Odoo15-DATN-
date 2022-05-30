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
    value = fields.Float(string="Value")
    type = fields.Char(string="Type")

    @api.model
    def create(self, vals):
        if vals:
            result = super(EstimationModuleSummary, self).create(vals)
            return result


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
        string="No", index=True, readonly=True, help='Use to arrange calculation sequence')
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

    @api.depends('activity_id.activity_type', 'persons', 'days', 'percent_effort', 'sequence')
    def _compute_mandays(self):
        ls_breakdown = self.env['module.breakdown.activity'].search([('activity_id', '=', self.activity_id.ids[0])])
        result_sequence = {}
        self.env['config.activity'].auto_increase_sequence(result_sequence, ls_breakdown)
        result_sequence['sequence'] = result_sequence['sequence'] - 1
        for record in self:
            if record.sequence == 0:
                record.sequence = result_sequence['sequence'] + 1

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
    activity_id = fields.Many2one('config.activity', string="Connect Module")
    
    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
    activity = fields.Char(string="Activity")
    effort = fields.Float(string="Effort", default=0, store=True, compute='_compute_total_effort')
    percent = fields.Float(string="Percentage (%)", default=0, store=True, compute='_compute_percentage')

    
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
                

