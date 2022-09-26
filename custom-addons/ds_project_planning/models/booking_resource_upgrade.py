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
    member_type = fields.Many2one('planning.member.type')

    @api.depends('booking_id.booking_upgrade_month', 'booking_id.effort_rate')
    def compute_effort_week(self):
        for record in self.booking_id.booking_upgrade_month:
            id_month_db = self.env['planning.calendar.resource'].search([('id', '=', record.booking_id.id or record.booking_id.id.origin)]).get_id_month_edit
            if record.booking_id.check_edit_effort == 'effort_month' and str(record.id.origin) in id_month_db:
                for week in self:
                    total_effort_week = 0
                    for rec in record.booking_id.booking_upgrade_day:
                        if week.start_date_week <= rec.start_date_day and week.end_date_week >= rec.start_date_day:
                            total_effort_week += (rec.effort_rate_day)

                    working_day = 5
                    week.effort_rate_week = total_effort_week/working_day
    

    @api.onchange('effort_rate_week')
    def check_edit_effort(self):
        for week in self:
            if week.env.user.has_group('project.group_project_manager') == False:
                if week.start_date_week <= date.today():
                    raise UserError(_(
                                'Can not edit (%(week)s) with Start Date (%(start)s) less than or equal Current Date (%(current)s).',
                                week=week.name, start=week.start_date_week, current=date.today()
                            ))
                
                if week.booking_id.inactive_date and week.start_date_week >= week.booking_id.inactive_date and week.booking_id.inactive == True:
                    raise UserError(_(
                                'Can not edit (%(week)s) with Start Date (%(start)s) greater than or equal Inactive Date (%(inactive_date)s).',
                                week=week.name, start=week.start_date_week, inactive_date=week.booking_id.inactive_date
                            ))

                if week.end_date_week <= week.booking_id.start_date or week.start_date_week > week.booking_id.end_date:
                    raise UserError(_(
                                'Can not edit (%(week)s) outside the range from (%(start_book)s) to (%(end_book)s).',
                                week=week.name, start_book=week.booking_id.start_date, end_book=week.booking_id.end_date
                            ))

    def common_check_effort_rate_week(self, check_effort_rate, message, start_date_week, end_date_week):
        for week in self:
            member_calendars_week = self.env['booking.resource.week'].search([('employee_id', '=', week.employee_id.id), ('id', '!=', week.id or week.id.origin)])
            total_effort_booked = 0
            for member_calendar in member_calendars_week:
                if member_calendar.booking_id.member_type.name != 'Shadow Time':
                    if start_date_week <= member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week\
                        or start_date_week <= member_calendar.start_date_week and end_date_week < member_calendar.end_date_week and end_date_week > member_calendar.start_date_week\
                        or start_date_week > member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week and start_date_week < member_calendar.end_date_week\
                        or start_date_week > member_calendar.start_date_week and end_date_week < member_calendar.end_date_week\
                        or start_date_week == member_calendar.end_date_week or end_date_week == member_calendar.start_date_week:
                        total_effort_booked += member_calendar.effort_rate_week
            if week.effort_rate_week + total_effort_booked > 100 and week.booking_id.member_type.name != 'Shadow Time':
                if total_effort_booked > 0 and total_effort_booked < 100:
                    week.effort_rate_week = 100 - total_effort_booked
                check_effort_rate['check'] = False
                check_effort_rate['total_effort_booked'] = total_effort_booked
                check_effort_rate['effort_rate'] = week.effort_rate_week
                message['employee'] = week.employee_id.name
                message['name'] = week.name
                message['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
                message['start_date'] = week.start_date_week
                message['end_date'] = week.end_date_week
            else:
                check_effort_rate['check'] = True

    @api.onchange('effort_rate_week')
    def check_effort_rate_week(self):
        for week in self:
            message={}
            check_effort_rate = {}
            week.common_check_effort_rate_week(check_effort_rate, message, week.start_date_week, week.end_date_week)
            if check_effort_rate['check'] == False:
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in the period from {start_date} to {end_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], end_date=message['end_date'], name=message['name'])
                warning = {
                                'warning': {
                                    'title': 'Warning!',
                                    'message': msg
                                }
                            }
                if check_effort_rate['effort_rate'] > 100:
                    week.effort_rate_week = 100
                    return warning
                elif message['effort_rate'] < 100:
                    return warning

    @api.constrains('effort_rate_week')
    def _effort_rate_when_close_form(self):
        for week in self:
            message={}
            check_effort_rate = {}
            week.common_check_effort_rate_week(check_effort_rate, message, week.start_date_week, week.end_date_week)
            if check_effort_rate['check'] == False:
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in the period from {start_date} to {end_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], end_date=message['end_date'], name=message['name'])
                raise UserError(msg)

    @api.onchange('effort_rate_week')
    def check_effort_week_over(self):
        for week in self:
            if week.effort_rate_week < 0 or week.effort_rate_week > 100:
                raise UserError(_('Week : Effort Rate greater than or equal to 0% & less than or equal to 100%.'))

    def check_effort_week_when_gen(self, check_effort_rate_week, message_week, start_date_week, end_date_week, employee_id, effort_week, member_type):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        member_calendars_week = self.env['booking.resource.week'].search([('employee_id', '=', employee_id.id), ('member_type', '!=', id_member_type)])
        total_effort_booked = 0
        for member_calendar in member_calendars_week:
            if member_type != 'Shadow Time':
                if start_date_week <= member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week\
                    or start_date_week <= member_calendar.start_date_week and end_date_week < member_calendar.end_date_week and end_date_week > member_calendar.start_date_week\
                    or start_date_week > member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week and start_date_week < member_calendar.end_date_week\
                    or start_date_week > member_calendar.start_date_week and end_date_week < member_calendar.end_date_week\
                    or start_date_week == member_calendar.end_date_week or end_date_week == member_calendar.start_date_week:
                    total_effort_booked += member_calendar.effort_rate_week
        if member_type != 'Shadow Time':
            check_effort_rate_week['check'] = False
            message_week['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
        else:
            check_effort_rate_week['check'] = True

    @api.constrains('effort_rate_week')
    def check_effort_week_over_when_close(self):
        for week in self:
            if week.effort_rate_week < 0 or week.effort_rate_week > 100:
                raise UserError(_('Week : Effort Rate greater than or equal to 0% & less than or equal to 100%.'))


    def check_effort_week_remaining_common(self):
        for week in self:
            days = self.env['booking.resource.day'].search([('employee_id', '=', week.employee_id.id), ('booking_id', '=', week.booking_id.id or week.booking_id.id.origin)])
            count_day = 0
            day_of_week = []
            for day in days:
                if week.start_date_week <= day.start_date_day and week.end_date_week >= day.start_date_day:
                    count_day += 1
                    day_of_week.append(day)
            total_effort_booked = 0
            if len(day_of_week) > 0:
                for rec in self.env['booking.resource.day'].search([('employee_id', '=', week.employee_id.id), ('start_date_day', '=', day_of_week[0].start_date_day), ('booking_id', '!=', day_of_week[0].booking_id.id)]):
                    total_effort_booked += rec.effort_rate_day

            remaining_effort = round(100 - total_effort_booked)
            if week.effort_rate_week > (remaining_effort * count_day)/5:
                raise UserError(_('Since %(name)s has only %(day_count)s days, the current amount of effort (%(effort_week)s) should not be greater than %(remaining)s.', name=week.name, \
                    effort_week=week.effort_rate_week, remaining=(remaining_effort * count_day)/5, day_count=count_day))

    @api.onchange('effort_rate_week')
    def check_effort_week_remaining_onchange(self):
        self.check_effort_week_remaining_common()

    @api.constrains('effort_rate_week')
    def check_effort_week_remaining_constrains(self):
        self.check_effort_week_remaining_common()


class BookingResourceWeekTemp(models.Model):
    _name = "booking.resource.week.temp"
    _description = "Planning Booking Resource Week Temp"

    name = fields.Char('Name', readonly=True)
    start_date_week = fields.Date('Start Date', readonly=True)
    end_date_week = fields.Date('End Date', readonly=True)
    effort_rate_week = fields.Float('Effort(%)', readonly=False, compute='compute_effort_week', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')


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
    member_type = fields.Many2one('planning.member.type')

    @api.depends('booking_id.booking_upgrade_week')
    def compute_effort_month(self):
        for record in self:
            if record.booking_id.check_edit_effort == 'effort_week':
                total_effort_week = 0
                for rec in record.booking_id.booking_upgrade_day:
                    if record.start_date_month <= rec.start_date_day and record.end_date_month >= rec.start_date_day:
                        total_effort_week += (rec.effort_rate_day)

                working_day = len(pd.bdate_range(record.start_date_month.strftime('%Y-%m-%d'),
                                            record.end_date_month.strftime('%Y-%m-%d')))
                if working_day > 0:
                    record.effort_rate_month = total_effort_week/working_day

    @api.onchange('effort_rate_month')
    def check_edit_effort(self):
        for month in self:
            actual_end_date = date.today()
            for week in month.booking_id.booking_upgrade_week:
                if month.start_date_month.month == week.start_date_week.month and month.start_date_month.year == week.start_date_week.year \
                    and week.start_date_week <= date.today() and week.end_date_week >= date.today():
                    actual_end_date = week.end_date_week
            if month.end_date_month <= actual_end_date and month.env.user.has_group('project.group_project_manager') == False:
                raise UserError(_(
                            'Can not edit (%(month)s) with End Date (%(end)s) less than or equal Current Date (%(current)s).',
                            month=month.name, end=month.end_date_month, current=actual_end_date
                        ))
            if month.booking_id.inactive_date and month.start_date_month >= month.booking_id.inactive_date and month.booking_id.inactive == True\
                and week.env.user.has_group('project.group_project_manager') == False:
                raise UserError(_(
                    'Can not edit (%(month)s) with Start Date (%(start)s) greater than or equal Inactive Date (%(inactive_date)s).',
                    month=month.name, start=month.start_date_month, inactive_date=month.booking_id.inactive_date
                ))                     
        
    @api.depends('effort_rate_month')
    def compute_man_month(self):
        for month in self:
            working_day = 0
            for week in month.booking_id.booking_upgrade_week:
                if month.start_date_month.month == week.start_date_week.month and month.start_date_month.year == week.start_date_week.year:
                    if week.start_date_week >= week.booking_id.start_date and week.start_date_week <= week.booking_id.end_date or\
                        week.end_date_week >= week.booking_id.start_date and week.end_date_week <= week.booking_id.end_date:
                        if week.start_date_week < week.booking_id.start_date:
                            start_date = week.booking_id.start_date
                        else:
                            start_date = week.start_date_week

                        if week.end_date_week > week.booking_id.end_date:
                            end_date = week.booking_id.end_date
                        else:
                            end_date = week.end_date_week
                        working_day += len(pd.bdate_range(start_date.strftime('%Y-%m-%d'),
                                            end_date.strftime('%Y-%m-%d')))
            month.man_month = round(working_day/20 * month.effort_rate_month/100, 3)

    @api.onchange('effort_rate_month')
    def check_effort_month_over(self):
        for month in self:
            if month.effort_rate_month < 0 or month.effort_rate_month > 100:
                raise UserError(_('Month : Effort Rate greater than or equal to 0% & less than or equal to 100%.')) 

    @api.onchange('effort_rate_month')
    def get_id_month_edit(self):
        month_id = ''
        for month in self:
            month_id += ' ' + str(month.id or month.id.origin)
        self.booking_id.get_id_month(month_id)

    def common_check_effort_rate_month(self, check_effort_rate, message, start_date_month, end_date_month):
        for month in self:
            member_calendars_month = self.env['booking.resource.month'].search([('employee_id', '=', month.employee_id.id), ('id', '!=', month.id or month.id.origin)])
            total_effort_booked = 0
            for member_calendar in member_calendars_month:
                if member_calendar.booking_id.member_type.name != 'Shadow Time':
                    if start_date_month <= member_calendar.start_date_month and end_date_month >= member_calendar.end_date_month\
                        or start_date_month <= member_calendar.start_date_month and end_date_month < member_calendar.end_date_month and end_date_month > member_calendar.start_date_month\
                        or start_date_month > member_calendar.start_date_month and end_date_month >= member_calendar.end_date_month and start_date_month < member_calendar.end_date_month\
                        or start_date_month > member_calendar.start_date_month and end_date_month < member_calendar.end_date_month\
                        or start_date_month == member_calendar.end_date_month or end_date_month == member_calendar.start_date_month:
                        total_effort_booked += member_calendar.effort_rate_month
            if month.effort_rate_month + total_effort_booked > 100 and month.booking_id.member_type.name != 'Shadow Time':
                if total_effort_booked > 0 and total_effort_booked < 100:
                    month.effort_rate_month = 100 - total_effort_booked
                elif total_effort_booked == 0:
                    month.effort_rate_month = month.booking_id.effort_rate
                else:
                    month.effort_rate_month = 0
                check_effort_rate['check'] = False
                check_effort_rate['total_effort_booked'] = total_effort_booked
                check_effort_rate['effort_rate'] = month.effort_rate_month
                message['employee'] = month.employee_id.name
                message['name'] = month.name
                message['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
                message['start_date'] = month.start_date_month
                message['end_date'] = month.end_date_month
            else:
                check_effort_rate['check'] = True

    @api.onchange('effort_rate_month')
    def check_effort_rate_month(self):
        for month in self:
            message={}
            check_effort_rate = {}
            month.common_check_effort_rate_month(check_effort_rate, message, month.start_date_month, month.end_date_month)
            if check_effort_rate['check'] == False:
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in the period from {start_date} to {end_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], end_date=message['end_date'], name=message['name'])
                warning = {
                                'warning': {
                                    'title': 'Warning!',
                                    'message': msg
                                }
                            }
                if check_effort_rate['effort_rate'] > 100:
                    month.effort_rate_month = 100
                    return warning
                elif message['effort_rate'] < 100:
                    return warning

    @api.constrains('effort_rate_month')
    def _effort_rate_when_close_form(self):
        for month in self:
            message={}
            check_effort_rate = {}
            month.common_check_effort_rate_month(check_effort_rate, message, month.start_date_month, month.end_date_month)
            if check_effort_rate['check'] == False:
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in the period from {start_date} to {end_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], end_date=message['end_date'], name=message['name'])
                raise UserError(msg)

    def check_effort_month_when_gen(self, check_effort_rate_month, message_month, start_date_month, end_date_month, employee_id, effort_month, member_type):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        member_calendars_month = self.env['booking.resource.month'].search([('employee_id', '=', employee_id.id), ('member_type', '!=', id_member_type)])
        total_effort_booked = 0
        for member_calendar in member_calendars_month:
            if member_type != 'Shadow Time':
                if start_date_month <= member_calendar.start_date_month and end_date_month >= member_calendar.end_date_month\
                    or start_date_month <= member_calendar.start_date_month and end_date_month < member_calendar.end_date_month and end_date_month > member_calendar.start_date_month\
                    or start_date_month > member_calendar.start_date_month and end_date_month >= member_calendar.end_date_month and start_date_month < member_calendar.end_date_month\
                    or start_date_month > member_calendar.start_date_month and end_date_month < member_calendar.end_date_month\
                    or start_date_month == member_calendar.end_date_month or end_date_month == member_calendar.start_date_month:
                    total_effort_booked += member_calendar.effort_rate_month
        if member_type != 'Shadow Time':
            check_effort_rate_month['check'] = False
            message_month['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
        else:
            check_effort_rate_month['check'] = True

    @api.constrains('effort_rate_month')
    def check_effort_month_over_when_close(self):
        for month in self:
            if month.effort_rate_month < 0 or month.effort_rate_month > 100:
                raise UserError(_('Month : Effort Rate greater than or equal to 0% & less than or equal to 100%.')) 


class BookingResourceMonthTemp(models.Model):
    _name = "booking.resource.month.temp"
    _description = "Planning Booking Resource Month Temp"

    name = fields.Char('Name', readonly=True)
    start_date_month = fields.Date('Start Date', readonly=True)
    end_date_month = fields.Date('End Date', readonly=True)
    effort_rate_month = fields.Float('Effort(%)', readonly=False, compute='compute_effort_month', store=True, digits=(12,2))
    man_month = fields.Float('Man Month', readonly=True, store=True, compute='compute_man_month')
    booking_id = fields.Many2one('planning.calendar.resource')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')


class BookingResourceDay(models.Model):
    _name = "booking.resource.day"
    _description = "Planning Booking Resource Day"

    name = fields.Char('Name', readonly=True)
    start_date_day = fields.Date('Start Date', readonly=True)
    end_date_day = fields.Date('End Date', readonly=True)
    effort_rate_day = fields.Float('Effort(%)', readonly=False, compute='compute_effort_day', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    day_temp_id = fields.Many2one('booking.resource.day.temp')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')

    @api.depends('booking_id.booking_upgrade_week', 'booking_id.booking_upgrade_month')
    def compute_effort_day(self):
        if self.booking_id.check_edit_effort == 'effort_week':
            for week in self.booking_id.booking_upgrade_week:
                len_total_day = 0
                for record in self:
                    if record.start_date_day >= week.start_date_week and record.start_date_day <= week.end_date_week:
                        len_total_day += 1

                for rec in self:
                    if rec.start_date_day >= week.start_date_week and rec.start_date_day <= week.end_date_week:
                        if len_total_day > 0:
                            rec.effort_rate_day = (week.effort_rate_week * 5)/len_total_day
        elif self.booking_id.check_edit_effort == 'effort_month':
            for record in self.booking_id.booking_upgrade_month:
                len_week = 0
                len_week_no_expired = 0
                effort_week_expired = 0
                id_month_db = self.env['planning.calendar.resource'].search([('id', '=', record.booking_id.id or record.booking_id.id.origin)]).get_id_month_edit
                if str(record.id.origin) in id_month_db:
                    for week in self.booking_id.booking_upgrade_week:
                        if record.start_date_month.month == week.start_date_week.month and record.start_date_month.year == week.start_date_week.year:
                            len_week += 1
                            if week.start_date_week > date.today():
                                if week.end_date_week >= week.booking_id.start_date and week.start_date_week <= week.booking_id.end_date:
                                    len_week_no_expired += 1
                            else:
                                effort_week_expired += week.effort_rate_week 
                    for rec in self.booking_id.booking_upgrade_week:
                        if record.start_date_month.month == rec.start_date_week.month and record.start_date_month.year == rec.start_date_week.year \
                            and rec.start_date_week > date.today() and rec.end_date_week >= rec.booking_id.start_date and rec.start_date_week <= rec.booking_id.end_date:
                            for day in self:
                                if rec.start_date_week <= day.start_date_day and rec.end_date_week >= day.end_date_day:
                                    if len_week - len_week_no_expired > 0:
                                        day.effort_rate_day = self.calculator_effort_week(record.effort_rate_month, effort_week_expired, len_week, len_week_no_expired)
                                    else:
                                        day.effort_rate_day = record.effort_rate_month

    def calculator_effort_week(self, effort_month_edit, effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - effort_week_expired) / len_week_no_expired



    def check_effort_day_when_gen(self, check_effort_rate_day, message_day, start_date_day, end_date_day, employee_id, member_type):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        member_calendars_day = self.env['booking.resource.day'].search([('employee_id', '=', employee_id.id), ('member_type', '!=', id_member_type)])
        total_effort_booked = 0
        for member_calendar in member_calendars_day:
            if member_type != 'Shadow Time':
                if start_date_day == member_calendar.start_date_day and end_date_day == member_calendar.end_date_day:
                    total_effort_booked += member_calendar.effort_rate_day
        if member_type != 'Shadow Time':
            check_effort_rate_day['check'] = False
            message_day['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
        else:
            check_effort_rate_day['check'] = True


class BookingResourceDay(models.Model):
    _name = "booking.resource.day.temp"
    _description = "Planning Booking Resource Day Temp"

    name = fields.Char('Name', readonly=True)
    start_date_day = fields.Date('Start Date', readonly=True)
    end_date_day = fields.Date('End Date', readonly=True)
    effort_rate_day = fields.Float('Effort(%)', readonly=False, store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')
