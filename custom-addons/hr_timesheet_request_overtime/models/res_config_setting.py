from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    timeoff_type_overtime = fields.Many2one(
        comodel_name='hr.leave.type', 
        string="Timeoff type", 
        domain="[('requires_allocation', '=', 'yes'), ('active', '=', True)]",
        default=lambda self: self.env.company.timeoff_type_overtime
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        res.update({
            'timeoff_type_overtime': company.timeoff_type_overtime.id,
        })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        if self.timeoff_type_overtime and self.timeoff_type_overtime.requires_allocation != 'yes':
            raise ValidationError(_("The selected Timeoff type must require allocation."))
        if self.timeoff_type_overtime != company.timeoff_type_overtime:
            company.write({'timeoff_type_overtime': self.timeoff_type_overtime.id})
 