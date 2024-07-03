from odoo import api, fields, models

class RenderAvatarForEmployee(models.Model):
    _inherit = 'hr.employee'

    avatar_name = fields.Html(compute='_compute_avatar_name', string='Avatar Name')

    @api.depends('name', 'image_1920')
    def _compute_avatar_name(self):
        for record in self:
            image_url = f'/web/image/hr.employee/{record.id}/avatar_128'
            record.avatar_name = f'<img src="{image_url}" style="height: 20px; width: 20px; border-radius: 50%;" /> {record.name}'