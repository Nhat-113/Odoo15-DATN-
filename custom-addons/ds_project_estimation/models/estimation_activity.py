from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

sequence_activity_global = 0
class Activities(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activities"
    _order = "sequence,id"
    _rec_name = "activity"

    sequence = fields.Integer(string="No", readonly=True, store=True, compute='_compute_sequence')
    module_id = fields.Many2one("estimation.module", string="Module")
    sequence_breakdown = fields.Integer(string="Sequence Activities Breakdown", store=True, default=1, compute ='_compute_sequence_breakdown')
    check_compute = fields.Char(string="Check compute", readonly=True)

    activity = fields.Char("Activity", required=True)
    effort = fields.Float(string="Effort", default=0, store=True, compute='_compute_total_effort')
    percent = fields.Float(string="Percentage", default=0)
    activity_type = fields.Selection([('type_1', 'Type 1'),
                                      ('type_2', 'Type 2'),
                                      ('type_3', 'Type 3')],
                                    string='Activity type', 
                                    required=True,
                                    default='type_2',
                                    help='Please select activity type'
                                    )
    activity_current = fields.Many2one("config.activity", 
                                       string="Activities", 
                                       store=True, 
                                       domain="[('module_id', '=', module_id), ('sequence', '!=', sequence)]")
    
    add_lines_breakdown_activity = fields.One2many('module.breakdown.activity', 'activity_id', string="Breakdown Activity")
    check_default = fields.Boolean(string="Check default", default=False)
    # domain_module_id = fields.Char(string="domain module id", readonly=True, store=True, compute='_compute_domain_module_id')

   
    # @api.depends('activity_type')
    # def _compute_domain_module_id(self):
    #     for record in self:
    #         record.domain_module_id = json.dumps(
    #             [('id', '=', record.module_id.id or record.module_id.id.origin)]
    #         )
    
    @api.onchange('activity_type')
    def _get_module_id(self):
        module = self.env['estimation.module'].search([('id', '=', self.module_id.id or self.module_id.id.origin)])
        self.module_id = module
            
    @api.depends('add_lines_breakdown_activity.mandays', 'activity_current')
    def _compute_total_effort(self):
        for record in self:
            final_manday = 0.0
            for item in record.add_lines_breakdown_activity:
                if item.mandays > 1000:
                    raise UserError('Expected (man-days) must be less than 1000 !')
                else:
                    final_manday += item.mandays 
            record.effort = final_manday

    @api.model
    def default_get(self, fields):
        result = super(Activities, self).default_get(fields)
        result.update({
            'check_compute': 'OK' #is required for compute sequence
        })
        return result


    def unlink(self):
        for item in self:
            effort_distribute = self.env['module.effort.activity'].search([('module_id', 'in', [item.module_id.id, False]), ('activity', '=', item.activity)])
            breakdown_activity = self.env['module.breakdown.activity'].search([('activity_id','=', item.id)])
            if effort_distribute:
                effort_distribute.unlink()
            if breakdown_activity:
                breakdown_activity.unlink()
        return super(Activities, self).unlink()

    
    # @api.depends('check_compute')
    # def _compute_sequence(self):
    #     max_sequence = self.module_id.sequence_activities
    #     global sequence_activity_global
    #     for rec in self:
    #         # if save activities mode
    #         if rec.id:
    #             sequence_activity_global = 0
    #             for item in self.module_id.module_effort_activity:
    #                 if item.activity == rec.activity:
    #                     item.sequence = max_sequence
    #                     rec.sequence = max_sequence
    #                     max_sequence += 1
    #         else: #if this is create new activity
    #             # max = record.sequence_activities
    #             # for rec in self:
    #             if max_sequence == 1 and sequence_activity_global <= 1:
    #                 max_sequence = max(item.sequence for item in rec.module_id.module_config_activity)
    #                 sequence_activity_global = max_sequence
    #             rec.sequence = sequence_activity_global + 1
    #             if rec.id or rec.id.origin == False:
    #                 sequence_activity_global += 1
    
    @api.depends('check_compute')
    def _compute_sequence(self):
        for record in self.module_id:
            # if save module mode
            if record.id:
                max = record.sequence_activities
                for rec in self:
                    if rec.id:
                        break
                    else:
                        rec.sequence = max
                        for item in record.module_effort_activity:
                            if rec.module_id.id == record.id and item.activity == rec.activity:
                                item.sequence = rec.sequence
                        max += 1
            else: #if this is create new activity
                max = record.sequence_activities
                for rec in self:
                    rec.sequence = max
                    if rec.id or rec.id.origin == False:
                        max += 1
    
    @api.depends('add_lines_breakdown_activity')
    def _compute_sequence_breakdown(self):
        model = 'module.breakdown.activity'
        sequence_field = 'sequence_breakdown'
        ls_data_fields = 'add_lines_breakdown_activity'
        for record in self:
            domain = [('activity_id', '=', record.id or record.id.origin)]
            self.env['estimation.work']._compute_sequence_all(record, model, domain, sequence_field, ls_data_fields)

    @api.onchange('add_lines_breakdown_activity')
    def check_duplicate_breakdowns(self):
        break_names = []
        for record in self.add_lines_breakdown_activity:
            break_names.append(record.activity)
        
        if len(break_names) != len(set(break_names)): # check duplicate
            raise UserError('Breadown Activity name already exists!')
        
class DataActivity(models.Model):
    """
    Describe Data Activity
    """
    _name = "data.activity"
    _description = "Data Activity"
    _order = "sequence,id"
    _rec_name = "activity"  

    sequence = fields.Integer(string="No", index=True, readonly=True, help='Use to arrange calculation sequence')
    activity = fields.Char("Activity", required=True)
    description = fields.Char("Description")
    activity_type = fields.Selection([('type_1', 'Type 1'),
                                      ('type_2', 'Type 2'),
                                      ('type_3', 'Type 3')],
                                    string='Activity type', 
                                    required=True,
                                    default='type_2',
                                    help='Please select activity type'
                                    )

    @api.model
    def create(self, vals):
        if vals:
            check = False
            for key in vals:
                if key == 'sequence':
                    check = True
            # if vals is not the default data
            if check == False:
                ls_data = self.env['data.activity'].search([])
                self.auto_increase_sequence(vals, ls_data)
                return super(DataActivity, self).create(vals)
            else:
                return super(DataActivity, self).create(vals) 
        

    def auto_increase_sequence(self, vals, ls_data):
        sequence_max = 0
        for record in ls_data:
            if record.sequence > sequence_max:
                sequence_max = record.sequence
        vals['sequence'] = sequence_max + 1