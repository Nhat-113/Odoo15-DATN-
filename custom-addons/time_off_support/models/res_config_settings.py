    
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    time_off_type_id = fields.Many2one('hr.leave.type', string='For Work From Home')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update({'time_off_type_id': company.time_off_type_id.id})
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        if self.time_off_type_id != company.time_off_type_id:
            company.write({'time_off_type_id': self.time_off_type_id.id})
