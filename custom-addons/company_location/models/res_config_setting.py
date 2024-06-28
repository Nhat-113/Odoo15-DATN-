from odoo import api, fields, models

class ResConfigSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    acceptance_distance = fields.Float("Acceptance Distance(meters)", config_parameter='company_location.acceptance_distance')
    
    @api.model
    def get_values(self):
        res = super(ResConfigSetting, self).get_values()
        company = self.env.company
        res.update({
            'acceptance_distance': company.acceptance_distance,  
        })
        return res

    def set_values(self):
        super(ResConfigSetting, self).set_values()
        company = self.env.company

        field_to_check = 'acceptance_distance'
        
        if self[field_to_check] != company[field_to_check]:
            company.write({field_to_check: self[field_to_check]})
