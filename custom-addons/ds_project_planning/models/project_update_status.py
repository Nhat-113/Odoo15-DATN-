from odoo import models, fields


class ProjectUpdate(models.Model):
    _inherit = 'project.update'

    check_action_update_booking = fields.Boolean(default=False, store=True, compute='set_effort_project_done')

    def set_effort_project_done(self):
        for record in self:
            if record.status == 'off_track':
                record.check_action_update_booking = True
                for booking_id in record.project_id.planning_calendar_resources:
                    self.env['booking.resource.day'].search([
                        ('start_date_day', '>', record.date),
                        ('booking_id', '=', booking_id.id)
                    ]).write({'effort_rate_day': 0})

                    booking_id.booking_upgrade_month.compute_effort_month()
                    booking_id.booking_upgrade_week.compute_effort_week()
                    booking_id.compute_total_effort_common()
                    


        