from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    past_limit_in_days = fields.Integer(string="Past Limit in Days",
        config_parameter='hr_holidays.past_limit_in_days')

    @api.onchange('past_limit_in_days')
    def _onchange_past_limit_in_day(self):
        if self.past_limit_in_days:            
            if self.past_limit_in_days < 0:
                self.past_limit_in_days = 0
    
    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()

        field_config_param_map = [
            ('past_limit_in_days', 'hr_holidays.past_limit_in_days'),
        ]

        for field, config_param in field_config_param_map:
            res[field] = ir_config.get_param(config_param)

        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter']
        
        field_config_param_map = [
            ('past_limit_in_days', 'hr_holidays.past_limit_in_days'),
        ]

        for field, config_param in field_config_param_map:
            if self[field] != ir_config.get_param(config_param):
                ir_config.set_param(config_param, self[field])
