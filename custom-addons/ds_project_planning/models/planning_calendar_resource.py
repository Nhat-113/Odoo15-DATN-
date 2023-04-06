# -*- coding: utf-8 -*-
import json
import pandas as pd

import calendar, time
import re
from email.policy import default
from attr import field
from numpy import require
from odoo import models, fields, api, registry, _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class PlanningCalendarResource(models.Model):
    _name = "planning.calendar.resource"
    _description = "Planning Booking Resource Of Project"
    _order = "employee_id, id, start_date"
    _rec_name = "employee_id"
    
    
    def _check_readonly_date(self):
        is_role_pm = self.env.user.has_group('project.group_project_manager')
        for resource in self:
            if is_role_pm == False and resource.check_upgrade_booking == True:
                resource.readonly_date = True
            else:
                resource.readonly_date = False
                
    def get_id_month(self, id_month):
        for resource in self:
            resource.env['planning.calendar.resource'].search([('id', '=', resource.id or resource.id.origin)]).write({
                # 'get_id_month_edit': id_month.split()
                'get_id_month_edit': id_month
            })

    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Member Name', required=True, help="Member name")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished working on project")
    duration = fields.Integer(string="Duration (Working day)", store=True, #compute='_compute_duration',
                              readonly=True, help="The duration of working time in the project", default=1)
    calendar_effort = fields.Float(string="Booking Effort (Man Month)", default=0, readonly=True, store=True) #compute='_compute_duration',
    effort_rate = fields.Float(string="Effort Rate",readonly=False, #, compute='_compute_effort_rate_default's #compute='_compute_duration',
                               store=True, default=100, digits=(12,2))
    role_ids = fields.Many2one('config.job.position', string='Roles', require=True)
    note = fields.Text(string='Note')
    member_type = fields.Many2one(
        'planning.member.type', string="Member Type")
    member_type_rate = fields.Float(
        related='member_type.rate', string="Member Type (%)")
    inactive = fields.Boolean(string="Inactive Member",
                              default=False, store=True)
    inactive_date = fields.Date(string='Inactive Date', help="The start date of the member's inactivity in the project.")
    check_upgrade_booking = fields.Boolean(default=False)
    booking_upgrade_week = fields.One2many('booking.resource.week', 'booking_id', string='Week') #, compute='_get_booking_resource'
    booking_upgrade_month = fields.One2many('booking.resource.month', 'booking_id', string='Month') #, compute='_get_booking_resource'
    booking_upgrade_day = fields.One2many('booking.resource.day', 'booking_id', string='Day') #, compute='_get_booking_resource'
    select_type_upgrade = fields.Selection([('month', 'Month'),
                                            ('week', 'Week')],
                                            required=False,
                                            default='month')
    check_edit_effort = fields.Char('Check edit effort')
    get_id_month_edit = fields.Char('ID edit month', store=True) #, compute='get_id_month'
    select_type_gen_week_month = fields.Selection([('generator_effort_rate', 'Effort Rate'),
                                                   ('generator_remaining_effort', 'Remaining Effort Rate')],
                                                    required=True,
                                                    default='generator_remaining_effort',
                                                    string='Generate Type')
    readonly_date = fields.Boolean(compute="_check_readonly_date", default=False, store=False)
    planning_role_id = fields.Many2one('planning.roles', string='Roles', require=True)
    role_id_domain = fields.Char(
        compute='_get_role_id_domain',
        readonly=True,
        store=False
    )
    
    # is_generate_success = fields.Boolean(string="Is Generate Success", default=False)
    # is_store = fields.Boolean(string="Is Store", default=False)
    
    
    
    
    @api.model
    def open_calendar_resource(self, project_id):
        target_project = self.env['project.project'].browse(project_id)

        return {
            "title": _("Booking Resource (%s)", target_project.name),
            # "name": _("Booking Resource (%s)", target_project.name),
            "type": "ir.actions.act_window",
            "res_model": "project.project",
            "view_id": self.env.ref('ds_project_planning.view_form_calendar_resource').id,
            # "views": [[self.env.ref('ds_project_planning.view_form_calendar_resource').id, "form"]],
            "target": "new",
            "res_id": project_id
        }
        
        

    def unlink(self):
        today = date.today()
        is_role_pm = self.env.user.has_group('project.group_project_manager')
        for calendar in self:
            # calendar.validate_block_any_action_user()
            if calendar.start_date < today and is_role_pm == False:
                raise UserError(_(
                        'Can not delete member (%(resource)s) with Start Date (%(start)s) < Current Date (%(current)s).',
                        resource=calendar.employee_id.name, start=calendar.start_date, current=today
                    ))

            calendar.booking_upgrade_day.unlink()
            calendar.booking_upgrade_week.unlink()
            calendar.booking_upgrade_month.unlink()
        return super(PlanningCalendarResource, self).unlink()

    

    @api.depends('start_date', 'end_date')
    def _get_role_id_domain(self):
        for resource in self:
            resource.role_id_domain = json.dumps(
                [('company_id', '=', resource.project_id.company_id.id)]
            )
    
    
    

    # @api.depends('start_date', 'end_date', 'inactive', 'inactive_date', 'effort_rate')
    # def _compute_duration(self):
    #     """ Calculates duration working time"""
    #     id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')])
    #     pd_date_range = pd.bdate_range
    #     for resource in self:
    #         # resource.validate_block_any_action_user()
    #         if resource.inactive == False and resource.start_date and resource.end_date:
    #             working_days = len(pd.bdate_range(resource.start_date.strftime('%Y-%m-%d'),
    #                                             resource.end_date.strftime('%Y-%m-%d')))
    #             resource.duration = working_days if working_days > 0 else 1

    #         elif resource.inactive == True and resource.start_date and resource.inactive_date:
    #                 working_days = len(pd.bdate_range(resource.start_date.strftime('%Y-%m-%d'),
    #                                                 resource.inactive_date.strftime('%Y-%m-%d')))
    #                 resource.duration = working_days if working_days > 0 else 1
    #         else:
    #             resource.duration = 1
                
    #         #compute effort rate
    #         # def _compute_effort_rate_default(self):
    #         if resource.start_date and resource.end_date and resource.employee_id.id:
    #             # resource.effort_rate = 100
    #             resource._common_check_effort_rate(id_member_type)
                
    #         # compute calendar effort
    #         # def _compute_calendar_effort(self):
    #         if resource.check_upgrade_booking == False:
    #             if resource.start_date and resource.end_date and resource.start_date < resource.end_date:
    #                 day_count = (resource.end_date - resource.start_date).days
    #                 list_start_end = self.compute_get_start_end_month(resource.start_date, resource.end_date, day_count)
    #                 booking_effort = 0
    #                 for i in range(0, len(list_start_end), 2):
    #                     start_date = list_start_end[i].strftime('%Y-%m-%d')
    #                     end_date = list_start_end[i+1].strftime('%Y-%m-%d')
    #                     working_day_actual = len(pd_date_range(start_date, end_date))

    #                     date_start = datetime(year=list_start_end[i].year, month=list_start_end[i].month, day=1).strftime('%Y-%m-%d')
    #                     date_end = datetime(year=list_start_end[i+1].year, month=list_start_end[i+1].month, day=calendar.monthrange(list_start_end[i+1].year, list_start_end[i+1].month)[1]).strftime('%Y-%m-%d')
                        
    #                     working_day_total = len(pd_date_range(date_start, date_end))
    #                     booking_effort += round((working_day_actual/working_day_total)*(resource.effort_rate/100), 2)
    #             else:
    #                 booking_effort = 1
    #             resource.calendar_effort = booking_effort
    #         else:
    #             total_man_month = sum(month.man_month for month in resource.booking_upgrade_month)
    #             resource.calendar_effort = total_man_month


    @api.onchange('start_date', 'end_date', 'inactive', 'inactive_date')
    def compute_duration(self):
        if self.inactive == False and self.start_date and self.end_date:
            working_days = len(pd.bdate_range(self.start_date.strftime('%Y-%m-%d'),
                                            self.end_date.strftime('%Y-%m-%d')))
            self.duration = working_days if working_days > 0 else 1

        elif self.inactive == True and self.start_date and self.inactive_date:
                working_days = len(pd.bdate_range(self.start_date.strftime('%Y-%m-%d'),
                                                self.inactive_date.strftime('%Y-%m-%d')))
                self.duration = working_days if working_days > 0 else 1
        else:
            self.duration = 1
            
    @api.onchange('duration', 'effort_rate')
    def compute_calendar_effort(self):
        pd_date_range = pd.bdate_range
        if self.check_upgrade_booking == False:
            if self.start_date and self.end_date and self.start_date < self.end_date:
                day_count = (self.end_date - self.start_date).days
                list_start_end = self.compute_get_start_end_month(self.start_date, self.end_date, day_count)
                booking_effort = 0
                for i in range(0, len(list_start_end), 2):
                    start_date = list_start_end[i].strftime('%Y-%m-%d')
                    end_date = list_start_end[i+1].strftime('%Y-%m-%d')
                    working_day_actual = len(pd_date_range(start_date, end_date))

                    date_start = datetime(year=list_start_end[i].year, month=list_start_end[i].month, day=1).strftime('%Y-%m-%d')
                    date_end = datetime(year=list_start_end[i+1].year, month=list_start_end[i+1].month, day=calendar.monthrange(list_start_end[i+1].year, list_start_end[i+1].month)[1]).strftime('%Y-%m-%d')
                    
                    working_day_total = len(pd_date_range(date_start, date_end))
                    booking_effort += round((working_day_actual/working_day_total)*(self.effort_rate/100), 2)
            else:
                booking_effort = 1
            self.calendar_effort = booking_effort
        else:
            total_man_month = sum(month.man_month for month in self.booking_upgrade_month)
            self.calendar_effort = total_man_month
            
            
    @api.onchange('start_date', 'end_date', 'duration')
    def compute_effort_rate(self):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')])
        if self.start_date and self.end_date and self.employee_id.id:
            # self.effort_rate = 100
            self._common_check_effort_rate(id_member_type)
    
    
    @api.onchange('inactive')
    def _set_inactive_date(self):
        # self.validate_block_any_action_user()
        self.check_upgrade_booking = False
        if self.inactive == False:
            self.inactive_date = False   
            
                    
    # @api.onchange('effort_rate')
    # def validate_effort_rate_remaining(self):
    #     self.validate_block_any_action_user()
        # id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')])
        # self._common_check_effort_rate(id_member_type)
    
    
    @api.onchange('start_date', 'end_date')
    def check_time_of_project(self):
        # for resource in self:
        # self.validate_block_any_action_user()
        # self.validate_duration_booking_member()
        if self.project_id.date_start == False or self.project_id.date == False:
            raise UserError('Start date and End date of the project cannot be empty.')
        
        else:
            if self.start_date and self.end_date:
                if self.start_date < self.project_id.date_start or self.start_date > self.project_id.date:
                    raise UserError(_('Member %(resource)s: Start Date (%(start_booking)s) of booking should be between start date (%(start)s) and end date (%(end)s) of project.',
                                    resource=self.employee_id.name, start_booking = self.start_date, 
                                    start=self.project_id.date_start, end=self.project_id.date))
            
                if self.end_date < self.project_id.date_start or self.end_date > self.project_id.date:
                    raise UserError(_('Member %(resource)s: End Date (%(end_booking)s) of booking should be between start date (%(start)s) and end date (%(end)s) of project.',
                                    resource=self.employee_id.name, end_booking = self.end_date, 
                                    start=self.project_id.date_start, end=self.project_id.date))
        
                if self.start_date > self.end_date:
                    raise ValidationError(_(
                        'Member %(resource)s: start date (%(start)s) must be earlier than end date (%(end)s).',
                        resource=self.employee_id.name, start=self.start_date, end=self.end_date,
                    ))

    
    # @api.onchange('member_type', 'select_type_gen_week_month')
    # def validate_is_generate_booking(self):
    #     self.validate_block_any_action_user()
        
    
    @api.onchange('booking_upgrade_week', 'booking_upgrade_month')
    def check_effort_week_month(self):
        if self.inactive == False:
            if self.select_type_upgrade == 'week':
                self.check_edit_effort = 'effort_week'
            else:
                self.check_edit_effort = 'effort_month'
           

    @api.onchange('booking_upgrade_day')
    def onchange_effort_rate(self):
        if self.booking_upgrade_day:
            self.effort_rate = sum(self.booking_upgrade_day.mapped('effort_rate_day')) / len(self.booking_upgrade_day)
            self.compute_calendar_effort()
                     
                     
    # @api.onchange('booking_upgrade_month')
    # def check_effort_month(self):
    #     # for resource in self:     
    #     if self.select_type_upgrade == 'month' and self.inactive==False:
    #         self.check_edit_effort = 'effort_month'
            
    #     if self.booking_upgrade_week and self.booking_upgrade_month:
    #         self.compute_total_effort_common()
    #     self.compute_calendar_effort()
    
    # @api.onchange('check_upgrade_booking')
    # def _get_booking_resource(self):
    #     for resource in self:
    #         resource.booking_upgrade_week = self.env['booking.resource.week'].search([('booking_id', '=', resource.id)])
    #         resource.booking_upgrade_month = self.env['booking.resource.month'].search([('booking_id', '=', resource.id)])
    #         resource.booking_upgrade_day = self.env['booking.resource.day'].search([('booking_id', '=', resource.id)])
    

    # @api.onchange('effort_rate')
    # def update_effort_month(self):
    #     # for resource in self:
    #     self.validate_block_any_action_user()
    #     for day in self.booking_upgrade_day:
    #         day.effort_rate_day = self.effort_rate   
        
    
    @api.constrains('employee_id', 'start_date', 'end_date')
    def gen_effort_week_month_when_create_booking(self):
        cr = self.env.cr
        user = self.env.user.id
        for resource in self:
            # resource.action_upgrade_booking()
            resource.check_upgrade_booking = False
            # resource.is_store = True
            resource.upgrade_booking_common(user, cr, resource.start_date, resource.end_date if resource.inactive == False else resource.inactive_date)
        # self.action_set_parameter_cronjob()
    
    
    @api.constrains('inactive', 'inactive_date', 'start_date', 'end_date')
    def validate_inactive_date(self):
        today = date.today()
        role_user_login = self.env.user.has_group('project.group_project_manager')
        for resource in self:
            resource.validate_role_access_action_project(role_user_login, today)
            
            if resource.inactive_date and resource.inactive == True:
                if resource.inactive_date < resource.start_date or resource.inactive_date > resource.end_date:
                   raise UserError(_('Member %(resource)s: Inactive date should be between start date (%(start)s) and end date (%(end)s).',
                                    resource=resource.employee_id.name, start=resource.start_date, end=resource.end_date))
                
                # Unasign member task
                # def _unassign_member_in_tasks(self):
                inactive_date = fields.Datetime.to_datetime(resource.inactive_date)
                tasks = self.env['project.task'].search(['&', '&', ('project_id', '=', resource.project_id.id), 
                                                                ('user_ids', 'in', resource.employee_id.user_id.id), 
                                                                ('date_start', '>=', inactive_date)])
                for task in tasks:
                    user_ids = [x for x in task.user_ids.ids if x != resource.employee_id.user_id.id]
                    task.write({'user_ids': [(6, 0, user_ids)]})
        
        issue_type_task = self.env['project.issues.type'].search([('name', 'in', ['Task', 'task'])])
        task_no_assign = self.env['project.task'].search_count([('project_id', '=', self.project_id.id),
                                                                ('issues_type', '=', issue_type_task.id),
                                                                ('user_ids', '=',False)])
        if task_no_assign > 0 and self.project_id.last_update_status not in ['off_track', 'on_hold']:
            self.project_id.write({'last_update_status': 'missing_resource'})
                 
            
    
    @api.constrains('calendar_effort', 'effort_rate')
    def _check_calendar_effort_rate(self):
        for resource in self:
            if resource.calendar_effort <= 0 or resource.effort_rate <= 0:
               raise UserError(_('Member %(resource)s: Booking Effort and Effort Rate cannot be less than or equal 0.', resource=resource.employee_id.name))


    # @api.constrains('inactive', 'inactive_date')
    # def _unassign_member_in_tasks(self):
    #     for resource in self.filtered(lambda r: r.inactive):
    #         # if resource.inactive:
    #             inactive_date = fields.Datetime.to_datetime(resource.inactive_date)

    #             tasks = self.env['project.task'].search(['&', '&', ('project_id', '=', resource.project_id.id), (
    #                 'user_ids', 'in', resource.employee_id.user_id.id), ('date_start', '>=', inactive_date)])
    #             for task in tasks:
    #                 user_ids = [x for x in task.user_ids.ids if x != resource.employee_id.user_id.id]
    #                 task.write({'user_ids': [(6, 0, user_ids)]})

    #     issue_type_task = self.env['project.issues.type'].search([('name', 'in', ['Task', 'task'])])
    #     task_no_assign = self.env['project.task'].search_count([('project_id', '=', self.project_id.id),
    #                                                             ('issues_type', '=', issue_type_task.id),
    #                                                             ('user_ids', '=',False)])
        
    #     if task_no_assign > 0:
    #         if self.project_id.last_update_status not in ['off_track', 'on_hold']:
    #             self.project_id.write({'last_update_status': 'missing_resource'})
                

    @api.constrains('member_type', 'planning_role_id', 'role_ids')
    def check_edit_member(self):
        today = date.today()
        role_user_login = self.env.user.has_group('project.group_project_manager')
        for calendar in self:
            calendar.validate_role_access_action_project(role_user_login, today)


    # @api.constrains('booking_upgrade_week', 'booking_upgrade_month')
    # def recompute_when_save(self):
    #     for resource in self:
    #         if resource.booking_upgrade_week and resource.booking_upgrade_month:
    #             resource.compute_total_effort_common()  

        
    def validate_role_access_action_project(self, is_role_pm, today):
        if is_role_pm == False and self.end_date < today:
            raise UserError(_(
                        'Can not edit member (%(resource)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        resource = self.employee_id.name, end = self.end_date, current = today
                    ))
    

    def _common_check_effort_rate(self, id_member_type):
        # for resource in self:
        if self.member_type.name != id_member_type.name:
            member_calendars = self.search([('employee_id', '=', self.employee_id.id), 
                                                                            ('id', '!=', self.id or self.id.origin),
                                                                            ('member_type', '!=', id_member_type.id)])
            total_effort_booked = 0
            for member_calendar in member_calendars:
                # if member_calendar.member_type.name != 'Shadow Time':
                if self.start_date <= member_calendar.start_date and self.end_date >= member_calendar.end_date\
                    or self.start_date <= member_calendar.start_date and self.end_date < member_calendar.end_date and self.end_date > member_calendar.start_date\
                    or self.start_date > member_calendar.start_date and self.end_date >= member_calendar.end_date and self.start_date < member_calendar.end_date\
                    or self.start_date > member_calendar.start_date and self.end_date < member_calendar.end_date\
                    or self.start_date == member_calendar.end_date or self.end_date == member_calendar.start_date:
                        
                    total_effort_booked += member_calendar.effort_rate
                        
            if self.effort_rate + total_effort_booked > 100:
                if total_effort_booked > 0 and total_effort_booked < 100:
                    self.effort_rate = 100 - total_effort_booked
                elif total_effort_booked == 0:
                    self.effort_rate = self.calendar_effort * 20 / self.duration * 100
                else:
                    self.effort_rate = 0
                
    
    # def count_total_month(self, start_date, end_date, day_count):
    def compute_get_start_end_month(self, start_date, end_date, day_count):
        # day_count = (end_date - start_date).days
        ls_start_end = [start_date]
        if self.is_month_end(start_date) == True:
            ls_start_end.append(start_date)
        
        # Create a pandas DataFrame with all the dates in the specified range
        df = pd.DataFrame(pd.date_range((start_date + timedelta(1)).strftime("%Y-%m-%d"), periods=day_count), columns=['date'])
        
        # Create a Series containing True/False values for the first and last days of each month
        is_month_start_end = df['date'].apply(lambda x: x.is_month_start or x.is_month_end)
        
        # Create a list of the first and last days of each month from the is_month_start_end Series
        arr_start_ends = df[is_month_start_end]['date'].apply(lambda x: datetime.strptime(x.strftime('%Y-%m-%d'), '%Y-%m-%d').date()).tolist()
        ls_start_end += arr_start_ends
        
        if self.is_month_end(end_date) == False:
            ls_start_end.append(end_date)
            
        return ls_start_end
    
    
    
    def check_effort_day_when_gen(self, start_date_day):
        id_member_type = self.env['planning.member.type'].search([('name', '=', 'Shadow Time')]).id
        member_calendars_day = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id),
                                                                        ('booking_id', '!=', self.id),
                                                                        ('member_type', '!=', id_member_type),
                                                                        ('start_date_day', '=', start_date_day)])
        total_effort_booked = 0
        if self.member_type.name != 'Shadow Time':
            total_effort_booked = sum(member_calendars_day.mapped('effort_rate_day'))
            
        return round((100 - total_effort_booked), 2) if total_effort_booked < 100 else 0
            
    
    def upgrade_booking_common(self, user, cr, start_date_common, end_date_common):
        cntday = (end_date_common - start_date_common).days
        day_count_day = cntday + 1
        no_day = 1
        # insert_field_defaults = "create_uid, write_uid, create_date, write_date"
        insert_vals_defaults = ", " + str(user) + ", " + str(user) + ", now(), now()" + " ); "
        
        # Generate booking day data
        sqlquerys = "DELETE FROM booking_resource_day WHERE booking_id = " + str(self.id) + '; '
        insert_qr = """INSERT INTO booking_resource_day (
                                    name, start_date_day, effort_rate_day, booking_id, employee_id, member_type, 
                                    create_uid, write_uid, create_date, write_date
                                )VALUES """
        
        # Handle week
        mon_sun = [start_date_common]
        if start_date_common.weekday() == 6 or self.is_month_end(start_date_common) == True:
            mon_sun.append(start_date_common)
        
        total_effort = 0
        for n in range(day_count_day):
            isdate = start_date_common + timedelta(n)
            indexday = isdate.weekday()
            
            # Handle days
            if indexday < 5:    # 5 is index of saturday in the week
                rs_efforts = self.check_effort_day_when_gen(isdate)
                if self.select_type_gen_week_month == 'generator_remaining_effort':
                    effort_day = self.effort_rate if self.effort_rate < rs_efforts else rs_efforts
                    
                elif self.select_type_gen_week_month == 'generator_effort_rate':
                    effort_day = self.effort_rate
                    
                vals = "('Day "  + str(no_day) + "', '" \
                            + str(isdate) + "', '" \
                            + str(effort_day) + "', '" \
                            + str(self.id) + "', '" \
                            + str(self.employee_id.id) + "', " \
                            + (str(self.member_type.id) if self.member_type.id else "NULL")
                
                sqlquerys += insert_qr + vals + insert_vals_defaults
                total_effort += effort_day
                no_day += 1
            
            #Handle week
            if n > 0:
                if indexday in [0, 6]:       # [Monday, Sunday]
                    mon_sun.append(isdate)
                if isdate.day == 1 and indexday != 0 or \
                    self.is_month_end(isdate) == True and int(len(mon_sun)) % 2 != 0:
                    mon_sun.append(isdate)
        self.excute_query_destroy_variable(cr, vals, insert_qr, sqlquerys)
        
        # Generate booking week data
        week_query = "DELETE FROM booking_resource_week WHERE booking_id = " + str(self.id) + " ;"
        week_insert = """INSERT INTO booking_resource_week (
                                    name, start_date_week, end_date_week, effort_rate_week, booking_id, employee_id, member_type,
                                    create_uid, write_uid, create_date, write_date
                                ) VALUES """
        if end_date_common.weekday() != 6 and self.is_month_end(end_date_common) != True:   # Index day of the Sunday = 6
            mon_sun.append(end_date_common)
        
        if len(mon_sun) % 2 != 0:
            mon_sun.append(end_date_common)
        no_week = 1
        for i in range(0, len(mon_sun), 2):
            effort_week = self.compute_effort_when_gen(mon_sun[i], mon_sun[i+1])

            vals = "('Week "  + str(no_week) + "', '" \
                        + str(mon_sun[i]) + "', '" \
                        + str(mon_sun[i+1]) + "', '" \
                        + str(effort_week) + "', '" \
                        + str(self.id) + "', '" \
                        + str(self.employee_id.id) + "', " \
                        + (str(self.member_type.id) if self.member_type.id else "NULL")
            week_query += week_insert + vals + insert_vals_defaults
            
            working_day_week = len(pd.bdate_range(mon_sun[i].strftime('%Y-%m-%d'),
                                                mon_sun[i+1].strftime('%Y-%m-%d')))
            if (len(mon_sun) - 1) - (i+3) >= 0:
                working_day_after_week = len(pd.bdate_range(mon_sun[i+2].strftime('%Y-%m-%d'),
                                                    mon_sun[i+3].strftime('%Y-%m-%d')))
                if working_day_week == 5 and working_day_after_week != 0 or working_day_week < 5 and working_day_after_week == 5:
                    no_week += 1
            else:
                no_week += 1
        self.excute_query_destroy_variable(cr, vals, week_insert, week_query)
        
        # Generate booking month data
        month_query = "DELETE FROM booking_resource_month WHERE booking_id = " + str(self.id) + "; "
        month_insert = """INSERT INTO booking_resource_month(
                                    name, start_date_month, end_date_month, effort_rate_month, man_month, booking_id, employee_id, member_type,
                                    create_uid, write_uid, create_date, write_date
                                ) VALUES """

        list_start_end = self.compute_get_start_end_month(start_date_common, end_date_common, cntday)
        total_mm = 0
        for i in range(0, len(list_start_end), 2):
            effort_months = self.compute_effort_month_when_gen(list_start_end[i], list_start_end[i+1])
            vals = "('Month "  + str(list_start_end[i].month) + "', '" \
                        + str(list_start_end[i]) + "', '" \
                        + str(list_start_end[i+1]) + "', '" \
                        + str(round(effort_months['effort_month'], 2)) + "', '" \
                        + str(round(effort_months['man_month'], 2)) + "', '" \
                        + str(self.id) + "', '" \
                        + str(self.employee_id.id) + "', " \
                        + (str(self.member_type.id) if self.member_type.id else "NULL")
            
            month_query += month_insert + vals + insert_vals_defaults
            total_mm += effort_months['man_month']
        self.excute_query_destroy_variable(cr, vals, month_insert, month_query)
        
        #Set status planning calendar resource
        self.check_upgrade_booking = True
        self.effort_rate = total_effort / (no_day - 1)
        self.calendar_effort = total_mm
        # self.is_generate_success = True

    
    def is_month_end(self, date):
        #check if date is the end of a month
        return date.day == calendar.monthrange(date.year, date.month)[1]
    
    def excute_query_destroy_variable(self, cr, vals, insert, query):
        cr.execute(query)
        cr.commit()
        # Destroy variable
        del vals
        del insert
        del query
    

    def compute_effort_when_gen(self, start_date, end_date, working_day = 5):
        booking_days = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                                ('booking_id', '=', self.id),
                                                                ('start_date_day', '>=', start_date),
                                                                ('start_date_day', '<=', end_date)])
        
        total_effort_week = sum(booking_days.mapped('effort_rate_day'))
        return total_effort_week/working_day
    

    def compute_effort_month_when_gen(self, start_date, end_date):
        start_date_month_actual = date(start_date.year, start_date.month, 1)
        end_date_month_actual = date(end_date.year, end_date.month, calendar.monthrange(end_date.year, end_date.month)[1])
        total_working_day = len(pd.bdate_range(start_date_month_actual.strftime('%Y-%m-%d'),
                                                    end_date_month_actual.strftime('%Y-%m-%d')))
        
        working_day = len(pd.bdate_range(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        booking_days = self.env['booking.resource.day'].search([('employee_id', '=', self.employee_id.id), 
                                                                ('booking_id', '=', self.id),
                                                                ('start_date_day', '>=', start_date),
                                                                ('start_date_day', '<=', end_date)])
        
        total_effort = sum(booking_days.mapped('effort_rate_day')) 
        man_month = 0
        if booking_days:
            man_month =  round((working_day / total_working_day) * ((total_effort / len(booking_days)) / 100), 2)
        
        return {
            'effort_month': total_effort/total_working_day,
            'man_month': man_month
        }
        

    # def action_upgrade_booking(self):
    #     self.write({
    #         'check_upgrade_booking': False
    #     })
    #     if self.inactive == False:          
    #         self.upgrade_booking_common(self.start_date, self.end_date)
    #     else:
    #         if self.inactive_date:
    #             self.upgrade_booking_common(self.start_date, self.inactive_date)
    #     self.compute_total_effort_common()


    def compute_total_effort_common(self):
        # booking_days = self.env['booking.resource.day'].search([('booking_id', '=', self.id),
        #                                                         ('start_date_day', '>=', self.start_date),
        #                                                         ('start_date_day', '<=', self.end_date)])
        booking_days = self.booking_upgrade_day
        effort_rate_total = 0
        if booking_days:
            total_effort = sum(booking_days.mapped('effort_rate_day'))
            effort_rate_total = total_effort / len(booking_days)
        self.effort_rate = effort_rate_total
        # self.env['planning.calendar.resource'].search([('id', '=', self.id or self.id.origin)]).write({
        #     'effort_rate' : effort_rate_total
        # })
            
    
    # def calculator_total_effort(self):
    #     self.compute_total_effort_common()
        

    def calculator_effort_month(self, effort_month_edit, total_effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - (total_effort_week_expired)) / len_week_no_expired

    
    def action_set_parameter_cronjob(self):
        """Action used to get booking_id for parameter to run ir_cron
            support generate data Month, Week, Day in the planning calendar resource
        """
        params = self.env['ir.config_parameter'].sudo().search([('key', '=', 'planning.generate_booking_support')])
        # params = self.env['ir.config_parameter'].sudo().get_param('planning.generate_booking_support')
        if params:
            vals = params.value if params.value == '' else params.value + ' '
            vals += ' '.join(str(id) for id in self.ids)
            params.value = vals
        else:
            vals = ' '.join(str(id) for id in self.ids)
            self.env['ir.config_parameter'].sudo().set_param(
                'planning.generate_booking_support', vals)
            
    def action_cronjob_generate_booking(self):
        params = self.env['ir.config_parameter'].sudo().get_param('planning.generate_booking_support')
        if params and params != '':
            params_ids = params.split(' ')
            params_ids = list(map(int, params_ids))
            
            booking_ids = self.search([('id', 'in', params_ids)], order='id', limit=5)
            cr = self.env.cr
            user = self.env.user.id
            for record in booking_ids:
                record.upgrade_booking_common(user, cr, record.start_date, record.end_date if record.inactive == False else record.inactive_date)
                
                strid = str(record.id) + ' ' if params.find(str(record.id) + ' ') != -1 else ' ' + str(record.id) if params.find(' ' + str(record.id)) != -1 else str(record.id)
                # params = re.sub(fr'\s*{record.id}\s*', '',params)
                params = params.replace(strid, '')
                # cr.execute("""UPDATE ir_config_parameter SET value = %s WHERE key = 'planning.generate_booking_support'; """, (params,))
                # cr.commit()
                self.env['ir.config_parameter'].sudo().set_param('planning.generate_booking_support', params)
        return 
    
    
    # def action_cronjob_update_value_batch(self):
    #     booking_resources = self.search([('project_id', '!=', False)], order="id")
    #     for booking in booking_resources:
    #         if booking.booking_upgrade_day and booking.booking_upgrade_week and booking.booking_upgrade_month or booking.inactive == True:
    #             booking.is_generate_success = True
    #             booking.is_store = True
    #     return
        
        
        
    # def validate_block_any_action_user(self):
    #     """ Action is block any action from user when planning_calendar_resource do not generate success (generate data month - week - day)
    #     """
    #     if self.is_generate_success == False and self.is_store == True:
    #         raise ValidationError(_('The booking member %(member)s is not allowed to edit or delete until the system completes the calculation and effort allocation functions.\
    #             \nPlease wait a few minutes', member= self.employee_id.name))
            
    # def validate_duration_booking_member(self):
    #     delta = relativedelta(self.end_date, self.start_date)
    #     cnt_month = delta.months + (delta.years * 12)
    #     if cnt_month > 12:
    #         raise ValidationError(_('Due to the extended booking period, which generates excessive data, booking beyond 12 months is not possible.'))
        
class PlanningAllocateEffortRate(models.Model):
    """ Type of member in project planning """
    _name = "planning.member.type"    
    _description = "Member Type of Project"
    _rec_name = "name"

    name = fields.Char('Name', required=True)
    rate = fields.Float(string='Rate', default=50.0)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Member Type name already exists!"),
    ]
