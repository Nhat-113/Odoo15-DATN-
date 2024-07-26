from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    time_off_type_id = fields.Many2one('hr.leave.type')
    time_off_type_unpaid_id = fields.Many2many('hr.leave.type')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update({
            'time_off_type_id': company.time_off_type_id.id,
            'time_off_type_unpaid_id': [(6, 0, company.time_off_type_unpaid_id.ids)]
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        if self.time_off_type_id != company.time_off_type_id:
            company.write({'time_off_type_id': self.time_off_type_id.id})
        if self.time_off_type_unpaid_id.ids != company.time_off_type_unpaid_id.ids:  
            company.write({'time_off_type_unpaid_id': [(6, 0, self.time_off_type_unpaid_id.ids)]})
