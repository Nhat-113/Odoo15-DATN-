from odoo import models, fields, api
from dateutil import tz


class ResourceCalendarLeaves(models.Model):
    _inherit = 'resource.calendar.leaves'
    
    date_start = fields.Date(string="Start date", store=True, compute='_compute_convert_datetime')
    date_end = fields.Date(string="End date", store=True, compute='_compute_convert_datetime')
    
    
    
    @api.depends('date_from', 'date_to')
    def _compute_convert_datetime(self):
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
        for record in self:
            start = record.date_from.replace(tzinfo=tz.UTC)
            end = record.date_to.replace(tzinfo=tz.UTC)
            record.date_start = start.astimezone(local_tz)
            record.date_end = end.astimezone(local_tz)
            
            # record.date_start = record.date_from.date()
            # record.date_end = record.date_to.date()