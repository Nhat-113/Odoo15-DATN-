from odoo import fields, models


class IrCron(models.Model):
    _inherit = 'ir.cron'

    smo_device_lc_schedule_ids = fields.Many2one('smo.device.lc.schedule', string="LC Schedule", ondelete='cascade')