from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date
import pandas as pd


class BookingResourceWeek(models.Model):
    _name = "booking.resource.week"
    _description = "Planning Booking Resource Week"

    name = fields.Char('Name', readonly=True)
    start_date_week = fields.Date('Start Date', readonly=True)
    end_date_week = fields.Date('End Date', readonly=True)
    effort_rate_week = fields.Float('Effort(%)', readonly=False, compute='compute_effort_week', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    week_temp_id = fields.Many2one('booking.resource.week.temp')
    employee_id = fields.Many2one('hr.employee')

    def calculator_effort_week(self, effort_month_edit, effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - effort_week_expired) / len_week_no_expired

    @api.depends('booking_id.booking_upgrade_month', 'booking_id.effort_rate')
    def compute_effort_week(self):
        i = 0
        for record in self.booking_id.booking_upgrade_month:
            len_week = 0
            len_week_no_expired = 0
            effort_week_expired = 0
            if record.booking_id.check_edit_effort == 'effort_month':
                for week in self:
                    if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year:
                        len_week += 1

                    if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year \
                        and week.start_date_week > date.today():
                        len_week_no_expired += 1 

                    if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year \
                        and week.start_date_week <= date.today():
                        effort_week_expired += week.effort_rate_week
                for rec in self:
                    if record.start_date_month.month == rec.start_date_week.month and record.start_date_month.year == rec.start_date_week.year \
                        and rec.start_date_week > date.today():
                        if len_week - len_week_no_expired > 0:
                            rec.effort_rate_week = self.calculator_effort_week(record.effort_rate_month, effort_week_expired, len_week, len_week_no_expired)
                        else:
                            rec.effort_rate_week = record.effort_rate_month
        
            i += 1

    @api.onchange('effort_rate_week')
    def check_edit_effort(self):
        for week in self:
            if week.start_date_week <= date.today():
               raise UserError(_(
                        'Can not edit (%(week)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        week=week.name, end=week.end_date_week, current=date.today()
                    ))


class BookingResourceWeek(models.Model):
    _name = "booking.resource.week.temp"
    _description = "Planning Booking Resource Week Temp"

    name = fields.Char('Name', readonly=True)
    start_date_week = fields.Date('Start Date', readonly=True)
    end_date_week = fields.Date('End Date', readonly=True)
    effort_rate_week = fields.Float('Effort(%)', readonly=False, compute='compute_effort_week', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    employee_id = fields.Many2one('hr.employee')

    def calculator_effort_week(self, effort_month_edit, effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - effort_week_expired) / len_week_no_expired

    @api.depends('booking_id.booking_upgrade_month', 'booking_id.effort_rate')
    def compute_effort_week(self):
        i = 0
        for record in self.booking_id.booking_upgrade_month:
            len_week = 0
            len_week_no_expired = 0
            effort_week_expired = 0
            for week in self:
                if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year:
                    len_week += 1

                if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year \
                    and week.start_date_week > date.today():
                    len_week_no_expired += 1 

                if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year \
                    and week.start_date_week <= date.today():
                    effort_week_expired += week.effort_rate_week
            for rec in self:
                if record.start_date_month.month == rec.start_date_week.month and record.start_date_month.year == rec.start_date_week.year \
                    and rec.start_date_week > date.today():
                    if len_week - len_week_no_expired > 0:
                        rec.effort_rate_week = self.calculator_effort_week(record.effort_rate_month, effort_week_expired, len_week, len_week_no_expired)
                    else:
                        rec.effort_rate_week = record.effort_rate_month
        
            i += 1

    @api.onchange('effort_rate_week')
    def check_edit_effort(self):
        for week in self:
            if week.start_date_week <= date.today():
               raise UserError(_(
                        'Can not edit (%(week)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        week=week.name, end=week.end_date_week, current=date.today()
                    ))

    

class BookingResourceMonth(models.Model):
    _name = "booking.resource.month"
    _description = "Planning Booking Resource Month"

    name = fields.Char('Name', readonly=True)
    start_date_month = fields.Date('Start Date', readonly=True)
    end_date_month = fields.Date('End Date', readonly=True)
    effort_rate_month = fields.Float('Effort(%)', readonly=False, compute='compute_effort_month', store=True, digits=(12,2))
    man_month = fields.Float('Man Month', readonly=True, store=True, compute='compute_man_month')
    booking_id = fields.Many2one('planning.calendar.resource')
    month_temp_id = fields.Many2one('booking.resource.month.temp')
    employee_id = fields.Many2one('hr.employee')

    @api.depends('booking_id.booking_upgrade_week')
    def compute_effort_month(self):
        i = 0
        for record in self:
            total_effort_month = 0
            len_total_week = 0
            if record.booking_id.check_edit_effort == 'effort_week':
                for rec in record.booking_id.booking_upgrade_week:
                    if record.start_date_month.month == rec.start_date_week.month and record.start_date_month.year == rec.start_date_week.year:
                        total_effort_month += (rec.effort_rate_week)
                        len_total_week += 1

                if len_total_week > 0:
                    record.effort_rate_month = total_effort_month/len_total_week
        
            i += 1

    @api.onchange('effort_rate_month')
    def check_edit_effort(self):
        for month in self:
            actual_end_date = date.today()
            for week in month.booking_id.booking_upgrade_week:
                if month.start_date_month.month == week.start_date_week.month and month.start_date_month.year == week.start_date_week.year \
                    and week.start_date_week <= date.today() and week.end_date_week >= date.today():
                    actual_end_date = week.end_date_week
            if month.end_date_month <= actual_end_date:
               raise UserError(_(
                        'Can not edit (%(month)s) with End Date (%(end)s) less than or equal Current Date (%(current)s).',
                        month=month.name, end=month.end_date_month, current=actual_end_date
                    ))
            else:
                month_id = month.id or month.id.origin
                month.booking_id.get_id_month(month_id)
        
    @api.depends('booking_id.booking_upgrade_month')
    def compute_man_month(self):
        for month in self:
            working_day = len(pd.bdate_range(month.start_date_month.strftime('%Y-%m-%d'),
                                            month.end_date_month.strftime('%Y-%m-%d')))
            month.man_month = working_day/20 * month.effort_rate_month/100


class BookingResourceMonth(models.Model):
    _name = "booking.resource.month.temp"
    _description = "Planning Booking Resource Month Temp"

    name = fields.Char('Name', readonly=True)
    start_date_month = fields.Date('Start Date', readonly=True)
    end_date_month = fields.Date('End Date', readonly=True)
    effort_rate_month = fields.Float('Effort(%)', readonly=False, compute='compute_effort_month', store=True, digits=(12,2))
    man_month = fields.Float('Man Month', readonly=True, store=True, compute='compute_man_month')
    booking_id = fields.Many2one('planning.calendar.resource')
    employee_id = fields.Many2one('hr.employee')

    @api.depends('booking_id.booking_upgrade_week')
    def compute_effort_month(self):
        i = 0
        for record in self:
            total_effort_month = 0
            len_total_week = 0
            for rec in record.booking_id.booking_upgrade_week:
                if record.start_date_month.month == rec.start_date_week.month and record.start_date_month.year == rec.start_date_week.year:
                    total_effort_month += (rec.effort_rate_week)
                    len_total_week += 1

            if len_total_week > 0:
                record.effort_rate_month = total_effort_month/len_total_week
        
            i += 1

    @api.onchange('effort_rate_month')
    def check_edit_effort(self):
        for month in self:
            actual_end_date = date.today()
            for week in month.booking_id.booking_upgrade_week:
                if month.start_date_month.month == week.start_date_week.month and month.start_date_month.year == week.start_date_week.year \
                    and week.start_date_week <= date.today() and week.end_date_week >= date.today():
                    actual_end_date = week.end_date_week
            if month.end_date_month <= actual_end_date:
               raise UserError(_(
                        'Can not edit (%(month)s) with End Date (%(end)s) less than or equal Current Date (%(current)s).',
                        month=month.name, end=month.end_date_month, current=actual_end_date
                    ))
        
    @api.depends('booking_id.booking_upgrade_month')
    def compute_man_month(self):
        for month in self:
            working_day = len(pd.bdate_range(month.start_date_month.strftime('%Y-%m-%d'),
                                            month.end_date_month.strftime('%Y-%m-%d')))
            month.man_month = working_day/20 * month.effort_rate_month/100