# from odoo import models, fields, api
# from dateutil import tz

# class HrLeave(models.Model):
#     _inherit = 'hr.leave'
    
    
#     date_start = fields.Date(string="Date Start Convert", store=True, compute='_compute_convert_date_time')
#     date_end = fields.Date(string="Date End Convert", store=True, compute='_compute_convert_date_time')
    
    
#     @api.depends('date_from', 'date_to')
#     def _compute_convert_date_time(self):
#         local_tz = tz.gettz('Asia/Ho_Chi_Minh')
#         for record in self:
#             start = record.date_from.replace(tzinfo=tz.UTC)
#             end = record.date_to.replace(tzinfo=tz.UTC)
#             record.date_start = start.astimezone(local_tz)
#             record.date_end = end.astimezone(local_tz)
    
