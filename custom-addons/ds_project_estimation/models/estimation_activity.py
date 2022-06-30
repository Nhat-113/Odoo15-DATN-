from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class Activities(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activities"
    _order = "sequence,id"
    _rec_name = "activity"

    sequence = fields.Integer(string="No") #, readonly=True, store=True, compute='_compute_sequence'
    module_id = fields.Many2one("estimation.module", string="Module")
    sequence_breakdown = fields.Integer(string="Sequence Activities Breakdown", store=True, default=1)
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
                                       domain="[('module_id', '=', module_id), ('activity', '!=', activity)]" )
    
    add_lines_breakdown_activity = fields.One2many('module.breakdown.activity', 'activity_id', string="Breakdown Activity")
    check_default = fields.Boolean(string="Check default", default=False)
    key_primary = fields.Char(string="Key Connect activity effort")
    # domain_module_id = fields.Char(string="domain module id", readonly=True, store=True, compute='_compute_domain_module_id')
    # domain_select_activities = fields.Char(string="Domain activities", readonly=True, store=True, compute='_compute_domain_activities')

   
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
        # self.activity_current = self.module_id.module_config_activity
            
    
    @api.depends('add_lines_breakdown_activity.mandays')
    def _compute_total_effort(self):
        for record in self:
            final_manday = 0.0
            for item in record.add_lines_breakdown_activity:
                if item.mandays > 1000 or item.mandays < 0:
                    raise UserError('Expected (man-days) must be less than 1000 and larger than 0!')
                else:
                    if item.type == 'type_1':
                        effort_activity_current = self.env['module.breakdown.activity']._find_effort_activity_current(record.module_id.module_config_activity, record.activity_current)
                        item.mandays = round((effort_activity_current * item.percent_effort)/ 100, 2)
                    elif item.type == 'type_3':
                        item.mandays = item.persons * item.days
                    else:
                        item.mandays = item.mandays_input
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
            item.add_lines_breakdown_activity.unlink()
        return super(Activities, self).unlink()

    @api.onchange('add_lines_breakdown_activity')
    def check_duplicate_breakdowns(self):
        break_names = []
        for index, record in enumerate(self.add_lines_breakdown_activity):
            break_names.append(record.activity)
            record.sequence = index + 1
        
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

    sequence = fields.Integer(string="No", index=True, help='Use to arrange calculation sequence')
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
    project_type = fields.Char(string="Project Type", required=True)
    
    _sql_constraints = [
            ('activity_uniq', 'unique (activity)', "Activity name already exists!"),
            ('sequence_uniq', 'unique (sequence)', "No. already exists!")
        ]

    @api.model
    def create(self, vals):
        if 'sequence' in vals:
            ls_data = self.env['data.activity'].search([])
            if ls_data:
                sequence_max = max(record.sequence for record in ls_data)
                vals['sequence'] = sequence_max + 1
        return super(DataActivity, self).create(vals)
