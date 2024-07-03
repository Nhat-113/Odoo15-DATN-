from odoo import fields, models

class IrCron(models.Model):
    _inherit = 'ir.cron'

    smo_device_lc_schedule_id_start = fields.Many2one('smo.device.lc.schedule', string="LC Schedule Start", ondelete='cascade')
    smo_device_lc_schedule_id_end = fields.Many2one('smo.device.lc.schedule', string="LC Schedule End", ondelete='cascade')