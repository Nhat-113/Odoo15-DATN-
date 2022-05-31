from odoo import models, fields, api, _


class Activities(models.Model):
    """
    Describe activities in configuration.
    """
    _name = "config.activity"
    _description = "Activities"
    _order = "sequence,id"
    _rec_name = "activity"

    sequence = fields.Integer(string="No", readonly=True, help='Use to arrange calculation sequence')
    estimation_id = fields.Many2one('estimation.work', string="Estimation") #default=lambda self: self.env.context['params']['id'], 

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
                                       default= 4, #4 is implementation
                                       domain="[('estimation_id', '=', estimation_id), ('sequence', '!=', sequence)]")
    
    add_lines_breakdown_activity = fields.One2many('module.breakdown.activity', 'activity_id', string="Breakdown Activity")

        
    @api.depends('add_lines_breakdown_activity.mandays', 'activity_current')
    def _compute_total_effort(self):
        final_manday = 0.0
        for record in self:
            for item in record.add_lines_breakdown_activity:
                final_manday += item.mandays 
            record.effort = final_manday

    @api.model
    def create(self, vals):
        if vals:
            # load sequence
            ls_activity = self.env['config.activity'].search([('estimation_id', '=', vals['estimation_id'])])
            self.env['config.activity'].auto_increase_sequence(vals, ls_activity)
            
            # check if values is default data or new data
            check = False
            is_data_default = False
            for key in vals:
                if key == 'add_lines_breakdown_activity':
                    check = True
                    for item in vals[key]:
                        if item[2] == 0:
                            is_data_default = True
                            break
                    break
                
            #if values is default data    
            if check == True and is_data_default == True:
                return super(Activities, self).create(vals)
            
            #if values is new data
            result = super(Activities, self).create(vals)
            ctx = {
                'sequence': vals['sequence'],
                'activity': vals['activity'],
                'effort': 0,
                'percent': 0,
                'estimation_id': vals['estimation_id'],
                'activity_id': result['id']
            }
            self.env['module.effort.activity'].create(ctx)
            return result

    def write(self, vals):
        if vals:
            effort_activity_vals = {}
            check = False
            for key in vals:
                if key == 'activity':
                    check = True
            if check == True:
                ls_effort_acivity = self.env['module.effort.activity'].search([('estimation_id', '=', self.estimation_id.id), ('sequence', '=', self.sequence )])
                effort_activity_vals['activity'] = vals['activity']
                ls_effort_acivity.write(effort_activity_vals)
                return super(Activities, self).write(vals)
            else:
                return super(Activities, self).write(vals)

    def unlink(self):
        for item in self:
            effort_distribute = self.env['module.effort.activity'].search([('estimation_id', '=', item.estimation_id.id), ('sequence', '=', item.sequence )])
            breakdown_activity = self.env['module.breakdown.activity'].search([('activity_id','=', item.id)])
            if effort_distribute:
                effort_distribute.unlink()
            if breakdown_activity:
                breakdown_activity.unlink()
        return super(Activities, self).unlink()

    def auto_increase_sequence(self, vals, ls_data):
        sequence_max = 0
        for record in ls_data:
            if record.sequence > sequence_max:
                sequence_max = record.sequence
        vals['sequence'] = sequence_max + 1
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
                self.env['config.activity'].auto_increase_sequence(vals, ls_data)
                return super(DataActivity, self).create(vals)
            else:
                return super(DataActivity, self).create(vals) 
        
    # def refresh_sequence(self):
    #     ls_data = self.env['data.activity'].search([])
    #     count = self.env['data.activity'].search_count([])
    #     index = 1
    #     for record in ls_data:
    #         if index < count:
    #             ls_data[index].sequence = record.sequence + 1
    #             index += 1
    #     return