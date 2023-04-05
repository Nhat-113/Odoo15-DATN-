from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date, datetime
from bisect import bisect_left, bisect_right
import pandas as pd
import calendar


class BookingResourceWeek(models.Model):
    _name = "booking.resource.week"
    _description = "Planning Booking Resource Week"

    name = fields.Char('Name', readonly=True)
    start_date_week = fields.Date('Start Date', readonly=True)
    end_date_week = fields.Date('End Date', readonly=True)
    effort_rate_week = fields.Float('Effort(%)', readonly=False, compute='compute_effort_week', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    # week_temp_id = fields.Many2one('booking.resource.week.temp')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')

    @api.depends('booking_id.booking_upgrade_month') #, 'booking_id.effort_rate'
    def compute_effort_week(self):
        month_edit = self.booking_id.get_id_month_edit
        if self.booking_id.check_edit_effort == 'effort_month':
            booking_months = self.env['booking.resource.month'].search([('id', '=', int(month_edit))])
            for week in self.filtered(lambda w: w.start_date_week >= booking_months.start_date_month and w.end_date_week <= booking_months.end_date_month):
                booking_days = self.booking_id.booking_upgrade_day.filtered(lambda d: d.start_date_day >= week.start_date_week\
                                                                                    and d.start_date_day <= week.end_date_week)
                
                total_effort_week = sum(booking_days.mapped('effort_rate_day'))
                week.effort_rate_week = total_effort_week/5
                
        elif self.booking_id.check_edit_effort == False and month_edit == False:
            for week in self:
                booking_days = self.booking_id.booking_upgrade_day.filtered(lambda d: d.start_date_day >= week.start_date_week\
                                                                                    and d.start_date_day <= week.end_date_week)
                total_effort_week = sum(booking_days.mapped('effort_rate_day'))
                week.effort_rate_week = total_effort_week/5
    
    
    @api.onchange('effort_rate_week')
    def check_edit_effort(self):
        if self.effort_rate_week < 0 or self.effort_rate_week > 100:
            raise UserError(_('Week %(name)s : Effort Rate greater than or equal to 0% & less than or equal to 100%.', name=self.name))
        
        if self.env.user.has_group('project.group_project_manager') == False:
            if self.start_date_week <= date.today():
                raise UserError(_(
                            'Can not edit (%(week)s) with Start Date (%(start)s) less than or equal Current Date (%(current)s).',
                            week=self.name, start=self.start_date_week, current=date.today()
                        ))
            
            if self.booking_id.inactive_date and self.start_date_week >= self.booking_id.inactive_date and self.booking_id.inactive == True:
                raise UserError(_(
                            'Can not edit (%(week)s) with Start Date (%(start)s) greater than or equal Inactive Date (%(inactive_date)s).',
                            week=self.name, start=self.start_date_week, inactive_date=self.booking_id.inactive_date
                        ))

            if self.end_date_week <= self.booking_id.start_date or self.start_date_week > self.booking_id.end_date:
                raise UserError(_(
                            'Can not edit (%(week)s) outside the range from (%(start_book)s) to (%(end_book)s).',
                            week=self.name, start_book=self.booking_id.start_date, end_book=self.booking_id.end_date
                        ))


    # def check_effort_week_when_gen(self, check_effort_rate_week, message_week, start_date_week, end_date_week, employee_id, effort_week, member_type):
    #     id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
    #     member_calendars_week = self.env['booking.resource.week'].search([('employee_id', '=', employee_id.id), ('member_type', '!=', id_member_type)])
    #     total_effort_booked = 0
    #     for member_calendar in member_calendars_week:
    #         if member_type != 'Shadow Time':
    #             if start_date_week <= member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week\
    #                 or start_date_week <= member_calendar.start_date_week and end_date_week < member_calendar.end_date_week and end_date_week > member_calendar.start_date_week\
    #                 or start_date_week > member_calendar.start_date_week and end_date_week >= member_calendar.end_date_week and start_date_week < member_calendar.end_date_week\
    #                 or start_date_week > member_calendar.start_date_week and end_date_week < member_calendar.end_date_week\
    #                 or start_date_week == member_calendar.end_date_week or end_date_week == member_calendar.start_date_week:
    #                 total_effort_booked += member_calendar.effort_rate_week
    #     if member_type != 'Shadow Time':
    #         check_effort_rate_week['check'] = False
    #         message_week['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
    #     else:
    #         check_effort_rate_week['check'] = True

    @api.constrains('effort_rate_week')
    def check_effort_week_over_when_close(self):
        for week in self:
            if week.effort_rate_week < 0 or week.effort_rate_week > 100:
                raise UserError(_('Week : Effort Rate greater than or equal to 0% & less than or equal to 100%.'))

    def check_effort_week_remaining_common(self):
            days = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                            ('booking_id', 'in', self.booking_id.ids),
                                                            ('start_date_day', '>=', self.start_date_week),
                                                            ('start_date_day', '<=', self.end_date_week)])
            id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
            total_effort_booked = 0
            count_day = len(days)
            
            if days:
            # Because during the week, the effort of the weekdays is the same => get only a day effort
                day_used_efforts = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                                        ('start_date_day', '=', days[0].start_date_day), 
                                                                        ('booking_id', 'not in', self.booking_id.ids), 
                                                                        ('member_type', '!=', id_member_type)])
                total_effort_booked = sum(day_used_efforts.mapped('effort_rate_day'))

            remaining_effort = round(100 - total_effort_booked)
            working_day = len(pd.bdate_range(self.start_date_week.strftime('%Y-%m-%d'),
                                            self.end_date_week.strftime('%Y-%m-%d')))
            if working_day > 0:
                if round(self.effort_rate_week) > (remaining_effort * count_day)/5 and self.booking_id.member_type.name != 'Shadow Time':
                    raise UserError(_('%(name)s : Can only book effort %(remaining)s for employee %(employee)s in project this', remaining=(remaining_effort * count_day)/5, \
                        name=self.name, employee=self.employee_id.name))
            else:
                if self.effort_rate_week > 0:
                    raise UserError('Do not edit the week with working day equal to 0.')

    @api.onchange('effort_rate_week')
    def check_effort_week_remaining_onchange(self):
        self.check_effort_week_remaining_common()


class BookingResourceMonth(models.Model):
    _name = "booking.resource.month"
    _description = "Planning Booking Resource Month"

    name = fields.Char('Name', readonly=True)
    start_date_month = fields.Date('Start Date', readonly=True)
    end_date_month = fields.Date('End Date', readonly=True)
    effort_rate_month = fields.Float('Effort(%)', readonly=False, compute='compute_effort_month', store=True, digits=(12,2))
    man_month = fields.Float('Man Month', readonly=True, store=True, compute='compute_man_month')
    booking_id = fields.Many2one('planning.calendar.resource')
    # month_temp_id = fields.Many2one('booking.resource.month.temp')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')
    effort_rate_month_actual = fields.Float('Effort Actual(%)', store=False, digits=(12,2))

    @api.depends('booking_id.booking_upgrade_week')
    def compute_effort_month(self):
        if self.booking_id.check_edit_effort in ['effort_week', False]:
            for month in self:
                booking_days = self.booking_id.booking_upgrade_day.filtered(lambda d: d.start_date_day >= month.start_date_month and d.start_date_day <= month.end_date_month)
                total_effort_day = sum(booking_days.mapped('effort_rate_day'))

                start_date_of_month = date(month.start_date_month.year, month.start_date_month.month, 1)
                end_date_of_month = date(month.start_date_month.year, month.start_date_month.month, calendar.monthrange(month.start_date_month.year, month.start_date_month.month)[1])
                working_day_of_month = len(pd.bdate_range(start_date_of_month.strftime('%Y-%m-%d'),
                                                        end_date_of_month.strftime('%Y-%m-%d')))

                if working_day_of_month > 0:
                    month.effort_rate_month = total_effort_day/working_day_of_month
                else:
                    month.effort_rate_month = 0

    @api.onchange('effort_rate_month')
    def check_edit_effort(self):
        today = date.today()
        actual_end_date = today
        # for week in self.booking_id.booking_upgrade_week:
        #     if self.start_date_month.month == week.start_date_week.month and self.start_date_month.year == week.start_date_week.year \
        #         and week.start_date_week <= today and week.end_date_week >= today:
        #         actual_end_date = week.end_date_week
        booking_weeks = self.env['booking.resource.week'].search([('booking_id', 'in', self.booking_id.ids),
                                                                  ('start_date_week', '>=', self.start_date_month),
                                                                  ('end_date_week', '<=', self.end_date_month),
                                                                  ('start_date_week', '<=', today),
                                                                  ('end_date_week', '>=', today)])
        if booking_weeks:
            actual_end_date = booking_weeks.end_date_week
                
        is_role_pm = self.env.user.has_group('project.group_project_manager')
        if is_role_pm == False:
            if self.end_date_month <= actual_end_date:
                raise UserError(_(
                            'Can not edit (%(month)s) with End Date (%(end)s) less than or equal Current Date (%(current)s).',
                            month=self.name, end=self.end_date_month, current=actual_end_date
                        ))
            if self.booking_id.inactive_date and self.start_date_month >= self.booking_id.inactive_date and self.booking_id.inactive == True:
                raise UserError(_(
                    'Can not edit (%(month)s) with Start Date (%(start)s) greater than or equal Inactive Date (%(inactive_date)s).',
                    month=self.name, start=self.start_date_month, inactive_date=self.booking_id.inactive_date
                ))                     
        
    @api.depends('effort_rate_month')
    def compute_man_month(self):
        for month in self:
            working_day_of_month = len(pd.bdate_range(month.start_date_month.strftime('%Y-%m-%d'),
                                                    month.end_date_month.strftime('%Y-%m-%d')))
            working_day_actual = len(pd.bdate_range(datetime(year=month.start_date_month.year, month=month.start_date_month.month, day=1).strftime('%Y-%m-%d'),
                                                        datetime(year=month.end_date_month.year, month=month.end_date_month.month, day=calendar.monthrange(month.end_date_month.year, month.end_date_month.month)[1]).strftime('%Y-%m-%d')))

            booking_days = month.booking_id.booking_upgrade_day.filtered(lambda d: d.start_date_day >= month.start_date_month and d.start_date_day <= month.end_date_month)
            effort_avg_day = sum(booking_days.mapped('effort_rate_day'))
            len_day = len(booking_days)
            if len_day > 0:
                month.man_month = round((working_day_of_month/working_day_actual) * ((effort_avg_day/len_day)/100), 2)
            else:
                month.man_month = 0


    @api.onchange('effort_rate_month')
    def get_id_month_edit(self):
        month_id = ''
        for month in self:
            month_id += ' ' + str(month.id or month.id.origin)
        self.booking_id.get_id_month(month_id)

    @api.constrains('effort_rate_month')
    def check_effort_month_over_when_close(self):
        for month in self:
            if month.effort_rate_month < 0 or month.effort_rate_month > 100:
                raise UserError(_('Month : Effort Rate greater than or equal to 0% & less than or equal to 100%.')) 

    def check_effort_month_remaining_common(self):
        days = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                        ('booking_id', 'in', self.booking_id.ids),
                                                        ('start_date_day', '>=', self.start_date_month),
                                                        ('start_date_day', '<=', self.end_date_month)])
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        count_day = len(days)
        total_effort_booked = 0
        if days:
            day_used_efforts = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                                    ('start_date_day', '=', days[0].start_date_day), 
                                                                    ('booking_id', 'not in', self.booking_id.ids), 
                                                                    ('member_type', '!=', id_member_type)])
            total_effort_booked = sum(day_used_efforts.mapped('effort_rate_day'))

        remaining_effort = round(100 - total_effort_booked)
        working_day = len(pd.bdate_range(self.start_date_month.strftime('%Y-%m-%d'),
                                        self.end_date_month.strftime('%Y-%m-%d')))
        if working_day > 0:
            if round(self.effort_rate_month) > (remaining_effort * count_day)/working_day and self.booking_id.member_type.name != 'Shadow Time':
                raise UserError(_('%(name)s : Can only book effort %(remaining)s for employee %(employee)s in project this', remaining=(remaining_effort * count_day)/working_day, \
                    name=self.name, employee=self.employee_id.name))

    @api.onchange('effort_rate_month')
    def check_effort_month_remaining_onchange(self):
        self.check_effort_month_remaining_common()

    @api.onchange('effort_rate_month')
    def check_edit_effort_warning(self):
        if self.effort_rate_month < 0 or self.effort_rate_month > 100:
            raise UserError(_('Month : Effort Rate greater than or equal to 0% & less than or equal to 100%.')) 
        
        if self.env.user.has_group('project.group_project_manager') == False:
            today = date.today()
            effort_total_edited = self.effort_rate_month * len(pd.bdate_range(self.start_date_month.strftime('%Y-%m-%d'),
                                                                                self.end_date_month.strftime('%Y-%m-%d')))

            day_expired = today    
            current_week = self.booking_id.booking_upgrade_week.filtered(lambda w: w.start_date_week <= today and w.end_date_week >= today)
            if current_week:
                day_expired = current_week.end_date_week
                
            booking_days = self.booking_id.booking_upgrade_day.filtered(lambda d: d.start_date_day < day_expired and d.start_date_day >= self.start_date_month and d.start_date_day <= self.end_date_month)
            effort_total_used = sum(booking_days.mapped('effort_rate_day'))

            if effort_total_edited < effort_total_used:
                raise UserError('Cannot edit effort rate less than total effort used')



class BookingResourceDay(models.Model):
    _name = "booking.resource.day"
    _description = "Planning Booking Resource Day"

    name = fields.Char('Name', readonly=True)
    start_date_day = fields.Date('Start Date', readonly=True)
    # end_date_day = fields.Date('End Date', readonly=True)
    effort_rate_day = fields.Float('Effort(%)', readonly=False, compute='compute_effort_day', store=True, digits=(12,2))
    booking_id = fields.Many2one('planning.calendar.resource')
    # day_temp_id = fields.Many2one('booking.resource.day.temp')
    employee_id = fields.Many2one('hr.employee')
    member_type = fields.Many2one('planning.member.type')
    
    def count_day_in_week(self, week):
        """
            Sử dụng thuật toán tìm kiếm nhị phân để đếm số ngày trong tuần
            điều kiện bát buộc là self phải được sắp xếp theo tự tăng dần.
            ở đây self là model booking.resource.day
        """
        start_dates = self.mapped('start_date_day')
        start_dates.sort()
        start_index = bisect_left(start_dates, week.start_date_week)
        end_index = bisect_right(start_dates, week.end_date_week)
        return end_index - start_index
    
    def compute_effort_rate_day_in_week(self, week, cnt_day):
        if cnt_day > 0:
            for day in self.filtered(lambda d: d.start_date_day >= week.start_date_week and d.start_date_day <= week.end_date_week):
                day.effort_rate_day = week.effort_rate_week * 5 / cnt_day
            
        

    @api.depends('booking_id.booking_upgrade_week', 'booking_id.booking_upgrade_month')
    def compute_effort_day(self):
        # for booking in self.booking_id:
            booking = self.booking_id
            if booking.check_edit_effort == 'effort_week' or booking.select_type_upgrade == 'week':
                for week in self.booking_id.booking_upgrade_week:
                    cnt_day = self.count_day_in_week(week)
                    self.compute_effort_rate_day_in_week(week, cnt_day)
                                
            elif booking.check_edit_effort == 'effort_month' or booking.select_type_upgrade == 'month':
                id_month_db = self.env['planning.calendar.resource'].search([('id', 'in', booking.ids)]).get_id_month_edit
                today = date.today()
                for record in booking.booking_upgrade_month:
                    days_in_month = self.filtered(lambda d: d.start_date_day >= record.start_date_month and d.start_date_day <= record.end_date_month)
                    weeks_in_month = booking.booking_upgrade_week.filtered(lambda w: w.start_date_week >= record.start_date_month and w.end_date_week <= record.end_date_month)
                    
                    if id_month_db and str(record.id or record.id.origin) in id_month_db:
                        if self.env.user.has_group('project.group_project_manager') == False:
                            len_day_no_expired = 0
                            effort_day_expired = 0
                            working_day = len(days_in_month)
                            
                            days_expired = [day for day in days_in_month if day.start_date_day < today]
                            len_day_no_expired = len(days_in_month) - len(days_expired)
                            effort_day_expired =  sum(day.effort_rate_day for day in days_expired)
                            
                            for week in weeks_in_month:
                                if week.start_date_week > today:
                                    days_in_week = [day for day in days_in_month if week.start_date_week <= day.start_date_day <= week.end_date_week]
                                    for day in days_in_week:
                                        day.effort_rate_day = record.effort_rate_month
                                        if working_day > len_day_no_expired and len_day_no_expired > 0:
                                            day.effort_rate_day = (record.effort_rate_month * working_day - effort_day_expired) / len_day_no_expired
                            
                            # for week in weeks_in_month:
                            #     for day in days_in_month.filtered(lambda d: d.start_date_day >= week.start_date_week and d.start_date_day <= week.end_date_week):
                            #         if week.start_date_week <= today:
                            #             effort_day_expired += day.effort_rate_day
                            #         else:
                            #             len_day_no_expired += 1
                            
                            # for week in weeks_in_month:
                            #     if week.start_date_week > today:
                            #         for day in days_in_month.filtered(lambda d: d.start_date_day >= week.start_date_week and d.start_date_day <= week.end_date_week):
                            #             day.effort_rate_day = record.effort_rate_month
                            #             if working_day > len_day_no_expired:
                            #                 day.effort_rate_day = (record.effort_rate_month * working_day - effort_day_expired) / len_day_no_expired

                        else:
                            for day in days_in_month:
                                day.effort_rate_day = record.effort_rate_month
                    else:
                        for week in weeks_in_month:
                            if self.validate_permission_access(week, today):
                                days_in_week = days_in_month.filtered(lambda d: d.start_date_day >= week.start_date_week and d.start_date_day <= week.end_date_week)
                                cnt_dayweek = len(days_in_week)
                                if cnt_dayweek > 0:
                                    for day in days_in_week:
                                        day.effort_rate_day = week.effort_rate_week * 5 / cnt_dayweek
                    

    def validate_permission_access(self, week, today):
        if self.env.user.has_group('project.group_project_manager'):
            return True
        return week.start_date_week > today

    def calculator_effort_week(self, effort_month_edit, effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - effort_week_expired) / len_week_no_expired

    # def check_effort_day_when_gen(self, check_effort_rate_day, message_day, start_date_day, end_date_day, employee_id, member_type):
    #     id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
    #     member_calendars_day = self.env['booking.resource.day'].search([('employee_id', '=', employee_id.id), ('member_type', '!=', id_member_type)])
    #     total_effort_booked = 0
    #     if member_type != 'Shadow Time':
    #         for member_calendar in member_calendars_day:
    #             if start_date_day == member_calendar.start_date_day and end_date_day == member_calendar.end_date_day:
    #                 total_effort_booked += member_calendar.effort_rate_day
    #         # if member_type != 'Shadow Time':
    #         check_effort_rate_day['check'] = False
    #         message_day['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
    #     else:
    #         check_effort_rate_day['check'] = True

    @api.constrains('effort_rate_day')
    def check_effort_month_over(self):
        for day in self:
            if day.effort_rate_day < 0 or day.effort_rate_day > 100:
                raise UserError(_('Day : Effort Rate greater than or equal to 0% & less than or equal to 100%.'))


    def common_check_effort_rate_day(self, check_effort_rate, message, start_date_day):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        for day in self:
            member_calendars_day = self.env['booking.resource.day'].search([('employee_id', '=', day.employee_id.id), 
                                                                            ('id', '!=', day.id or day.id.origin), 
                                                                            ('start_date_day', '=', start_date_day),
                                                                            ('member_type', '!=', id_member_type)])
            # total_effort_booked = sum(member_calendars_day.mapped('effort_rate_day'))
            # for member_calendar in member_calendars_day:
            #     if member_calendar.booking_id.member_type.name != 'Shadow Time':
            #         if start_date_day == member_calendar.start_date_day and end_date_day == member_calendar.end_date_day:
            #             total_effort_booked += member_calendar.effort_rate_day
                        
            total_effort_booked = sum(member_calendars_day.mapped('effort_rate_day'))         
                        
            if day.effort_rate_day + total_effort_booked > 100 and day.booking_id.member_type.name != 'Shadow Time':
                if day.booking_id.select_type_gen_week_month == 'generator_remaining_effort':
                    if total_effort_booked > 0 and total_effort_booked < 100:
                        day.effort_rate_day = 100 - total_effort_booked
                    elif total_effort_booked == 0:
                        day.effort_rate_day = day.booking_id.effort_rate
                    else:
                        day.effort_rate_day = 0
                check_effort_rate['check'] = False
                check_effort_rate['total_effort_booked'] = total_effort_booked
                check_effort_rate['effort_rate'] = day.effort_rate_day
                message['employee'] = day.employee_id.name
                message['name'] = day.name
                message['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
                message['start_date'] = day.start_date_day
                message['end_date'] = day.start_date_day
            else:
                check_effort_rate['check'] = True

    @api.onchange('effort_rate_day')
    def check_effort_rate_day(self):
        for day in self:
            message={}
            check_effort_rate = {}
            day.common_check_effort_rate_day(check_effort_rate, message, day.start_date_day)
            if check_effort_rate['check'] == False and day.effort_rate_day > message['effort_rate']:
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in day {start_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], name=message['name'])
                warning = {
                                'warning': {
                                    'title': 'Warning!',
                                    'message': msg
                                }
                            }
                if check_effort_rate['effort_rate'] > 100:
                    day.effort_rate_day = 100
                    return warning
                elif message['effort_rate'] < 100:
                    return warning

    @api.constrains('effort_rate_day')
    def _effort_rate_when_close_form(self):
        for day in self:
            message={}
            check_effort_rate = {}
            day.common_check_effort_rate_day(check_effort_rate, message, day.start_date_day)
            if check_effort_rate['check'] == False and round(day.effort_rate_day, 2) > round(message['effort_rate'], 2):
                msg = "{name}: Employee {employee} has ({effort_rate}%) Effort Rate in day {start_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], name=message['name'])
                raise UserError(msg) 


# class BookingResourceDayTemp(models.Model):
#     _name = "booking.resource.day.temp"
#     _description = "Planning Booking Resource Day Temp"

#     name = fields.Char('Name', readonly=True)
#     start_date_day = fields.Date('Start Date', readonly=True)
#     end_date_day = fields.Date('End Date', readonly=True)
#     effort_rate_day = fields.Float('Effort(%)', readonly=False, store=True, digits=(12,2))
#     booking_id = fields.Many2one('planning.calendar.resource')
#     employee_id = fields.Many2one('hr.employee')
#     member_type = fields.Many2one('planning.member.type')
