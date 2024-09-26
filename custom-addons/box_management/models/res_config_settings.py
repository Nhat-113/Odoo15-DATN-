from odoo import models, fields, api, _



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    attendance_view_type = fields.Boolean(string=_("Attendance view multiple records"), default=False, store=True)
    
    
    
        
    @api.model
    def get_values(self):
        result = super(ResConfigSettings, self).get_values()
        company = self.env.company
        result.update({
            'attendance_view_type': company.attendance_view_type
        })
        return result
    
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        if self.attendance_view_type != company.attendance_view_type:
            company.write({'attendance_view_type': self.attendance_view_type})
        