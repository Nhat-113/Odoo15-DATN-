# -*- coding: utf-8 -*-
import pandas as pd

import calendar
from email.policy import default
from attr import field
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class PlanningCalendarResource(models.Model):
    _name = "planning.calendar.resource"
    _description = "Planning Booking Resource Of Project"
    _order = "start_date"
    _rec_name = "employee_id"

    project_id = fields.Many2one(
        'project.project', string='Project', required=True, ondelete='cascade', help="Project", index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Member Name', required=True, help="Member name")
    start_date = fields.Date(string='Start Date', readonly=False, required=True, help="Date on which the member started working on project",
                             default=fields.Date.today)
    end_date = fields.Date(string='End Date', readonly=False, required=True,
                           help="Date on which the member finished working on project")
    duration = fields.Integer(compute='_compute_duration', string="Duration (Working day)",
                              readonly=True, help="The duration of working time in the project", default=1)
    calendar_effort = fields.Float(string="Booking Effort (Man Month)", default=0, compute='_compute_calendar_effort', readonly=True)
    effort_rate = fields.Float(string="Effort Rate", compute='_compute_effort_rate_default',readonly=False,
                               help="Effort Rate (%) = Booking Effort * 20 / Duration", store=True, default=0, digits=(12,2))
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
    booking_upgrade_week = fields.One2many('booking.resource.week', 'booking_id', string='Week', compute='_get_booking_resource')
    booking_upgrade_month = fields.One2many('booking.resource.month', 'booking_id', string='Month', compute='_get_booking_resource')
    select_type_upgrade = fields.Selection([('month', 'Month'),
                                            ('week', 'Week')],
                                            required=False,
                                            default='month')
    check_edit_effort = fields.Char('Check edit effort')
    get_id_month_edit = fields.Char('ID edit month', store=True, compute='get_id_month')

    @api.depends('start_date', 'end_date', 'inactive', 'inactive_date')
    def _compute_duration(self):
        """ Calculates duration working time"""
        for resource in self:
            if resource.inactive == False:
                if resource.end_date and resource.start_date:
                    working_days = len(pd.bdate_range(resource.start_date.strftime('%Y-%m-%d'),
                                                    resource.end_date.strftime('%Y-%m-%d')))
                    resource.duration = working_days if working_days > 0 else 1
                else:
                    resource.duration = 1
            else:
                if resource.start_date and resource.inactive_date:
                    working_days = len(pd.bdate_range(resource.start_date.strftime('%Y-%m-%d'),
                                                    resource.inactive_date.strftime('%Y-%m-%d')))
                    resource.duration = working_days if working_days > 0 else 1
                else:
                    resource.duration = 1

    def get_id_month(self, id_month=''):
        for resource in self:
            resource.env['planning.calendar.resource'].search([('id', '=', resource.id or resource.id.origin)]).write({
                'get_id_month_edit': id_month.split()
            })

    @api.onchange('inactive')
    def _set_inactive_date(self):
        if self.inactive == False:
            self.inactive_date = False                                             

    @api.onchange('inactive_date')
    def _upgrade_booking_inactive_date(self):
        for resource in self:
            resource.select_type_upgrade = 'week'
            resource.check_edit_effort = 'effort_week'
            for week in resource.booking_upgrade_week:
                if resource.inactive_date and week.start_date_week >= resource.inactive_date:
                    week.effort_rate_week = 0
            resource.booking_upgrade_month.compute_effort_month()
            

    @api.constrains('inactive_date', 'start_date', 'end_date')
    def validate_inactive_date(self):
        for resource in self:
            if resource.inactive_date and resource.inactive == True:
                if resource.inactive_date < resource.start_date or resource.inactive_date > resource.end_date:
                   raise UserError(_('Member %(resource)s: Inactive date should be between start date (%(start)s) and end date (%(end)s).',
                                    resource=resource.employee_id.name, start=resource.start_date, end=resource.end_date))
    
    @api.constrains('start_date', 'end_date', 'employee_id', 'effort_rate', 'member_type')
    def _effort_rate_when_close_form(self):
        for resource in self:
            message={}
            check_effort_rate = {}
            resource._common_check_effort_rate(check_effort_rate, message)
            if check_effort_rate['check'] == False:
                msg = "Over effort was assigned to the member {employee} for the time period ({start_date} to {end_date}).".format(employee=message['employee'],\
                        start_date=message['start_date'], end_date=message['end_date'])
                raise UserError(msg)

    @api.onchange('start_date', 'end_date')
    def _calculate_default_calendar_effort(self):
        if self.start_date and self.end_date:
            self.calendar_effort = self.duration / 20
            self.check_upgrade_booking = False

    @api.onchange('duration', 'calendar_effort')
    def _compute_effort_rate(self):
        """ Calculates effort rate (%)"""
        for resource in self:
            if resource.duration != 0:
                resource.effort_rate = resource.calendar_effort * 20 / resource.duration * 100

    @api.onchange('start_date', 'end_date', 'duration')
    def _compute_effort_rate_default(self):
        if self.start_date and self.end_date and self.employee_id.id:
            check_effort_rate = {}
            self._common_check_effort_rate(check_effort_rate, message={})

    @api.depends('duration', 'effort_rate')
    def _compute_calendar_effort(self):
        for resource in self:
            if resource.duration != 0:
                resource.calendar_effort = (resource.effort_rate * resource.duration) / (20 * 100)

            if resource.inactive_date == False:
                resource.select_type_upgrade = 'month'        

    def _check_dates(self):
        for resource in self:
            if resource.end_date and resource.start_date > resource.end_date:
                raise ValidationError(_(
                    'Member %(resource)s: start date (%(start)s) must be earlier than end date (%(end)s).',
                    resource=resource.employee_id.name, start=resource.start_date, end=resource.end_date,
                ))
    
    @api.constrains('calendar_effort', 'effort_rate')
    def _check_calendar_effort_rate(self):
        for resource in self:
            if resource.calendar_effort <= 0 or resource.effort_rate <= 0:
               raise UserError(_('Member %(resource)s: Booking Effort and Effort Rate cannot be less than or equal 0.', resource=resource.employee_id.name,))

    @api.constrains('start_date', 'end_date')
    def _check_start_end(self):   
        return self._check_dates()

    @api.onchange('start_date', 'end_date', 'member_type', 'effort_rate', 'employee_id')
    def _check_effort_rate(self):
        if self.start_date and self.end_date and self.employee_id.id:
            message={}
            check_effort_rate = {}
            self._common_check_effort_rate(check_effort_rate, message)
            if check_effort_rate['check'] == False:
                msg = "Employee {employee} has ({effort_rate}%) Effort Rate in the period from {start_date} to {end_date}.".format(employee=message['employee'],\
                            effort_rate=message['effort_rate'], start_date=message['start_date'], end_date=message['end_date'])
                warning = {
                                'warning': {
                                    'title': 'Warning!',
                                    'message': msg
                                }
                            }
                if check_effort_rate['effort_rate'] > 100:
                    self.effort_rate = 100
                    return warning
                elif message['effort_rate'] < 100:
                    return warning

    def _common_check_effort_rate(self, check_effort_rate, message):
        for resource in self:
            member_calendars = self.env['planning.calendar.resource'].search([('employee_id', '=', resource.employee_id.id), ('id', '!=', resource.id or resource.id.origin)])
            total_effort_booked = 0
            for member_calendar in member_calendars:
                if member_calendar.member_type.name != 'Shadow Time':
                    if resource.start_date <= member_calendar.start_date and resource.end_date >= member_calendar.end_date\
                        or resource.start_date <= member_calendar.start_date and resource.end_date < member_calendar.end_date and resource.end_date > member_calendar.start_date\
                        or resource.start_date > member_calendar.start_date and resource.end_date >= member_calendar.end_date and resource.start_date < member_calendar.end_date\
                        or resource.start_date > member_calendar.start_date and resource.end_date < member_calendar.end_date\
                        or resource.start_date == member_calendar.end_date or resource.end_date == member_calendar.start_date:
                        total_effort_booked += member_calendar.effort_rate
            if resource.effort_rate + total_effort_booked > 100 and resource.member_type.name != 'Shadow Time':
                if total_effort_booked > 0 and total_effort_booked < 100:
                    resource.effort_rate = 100 - total_effort_booked
                elif total_effort_booked == 0:
                    resource.effort_rate = resource.calendar_effort * 20 / resource.duration * 100
                else:
                    resource.effort_rate = 0
                check_effort_rate['check'] = False
                check_effort_rate['total_effort_booked'] = total_effort_booked
                check_effort_rate['effort_rate'] = resource.effort_rate
                message['employee'] = resource.employee_id.name
                message['effort_rate'] = round((100 - total_effort_booked), 2) if round((100 - total_effort_booked), 2) > 0 else 0
                message['start_date'] = resource.start_date
                message['end_date'] = resource.end_date
            else:
                check_effort_rate['check'] = True
                            
                            

    @api.constrains('inactive', 'inactive_date')
    def _unassign_member_in_tasks(self):
        for resource in self:
            if resource.inactive:
                inactive_date = fields.Datetime.to_datetime(
                    resource.inactive_date)

                tasks = self.env['project.task'].search(['&', '&', ('project_id', '=', resource.project_id.id), (
                    'user_ids', 'in', resource.employee_id.user_id.id), ('date_start', '>=', inactive_date)])
                for task in tasks:
                    user_ids = [x for x in task.user_ids.ids if x !=
                                resource.employee_id.user_id.id]
                    task.write({'user_ids': [(6, 0, user_ids)]})

        for project in resource.project_id:
            # calendars = self.env['planning.calendar.resource'].search(['&', ('project_id', '=', project.id), ('inactive', '=', True)])
            task_no_assign = self.env['project.task'].search_count(['&',('project_id', '=', project.id),('issues_type','=',1),('user_ids','=',False)])
            if task_no_assign > 0:
                # for calendar in calendars:
                if project.last_update_status not in ['off_track', 'on_hold']:
                    project.write({'last_update_status': 'missing_resource'})

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
        for calendar in self:
            if calendar.end_date < date.today() and calendar.env.user.has_group('project.group_project_manager') == False:
                raise UserError(_(
                        'Can not delete member (%(resource)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        resource=calendar.employee_id.name, end=calendar.end_date, current=date.today()
                    ))

            self.env['booking.resource.week'].search([('booking_id', '=', calendar.id)]).unlink()
            self.env['booking.resource.month'].search([('booking_id', '=', calendar.id)]).unlink()
        return super(PlanningCalendarResource, self).unlink()

    def write(self, vals):
        for calendar in self:
            if calendar.end_date < date.today() and calendar.env.user.has_group('project.group_project_manager') == False:
                raise UserError(_(
                        'Can not edit member (%(resource)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        resource=calendar.employee_id.name, end=calendar.end_date, current=date.today()
                    ))
            
        return super(PlanningCalendarResource, self).write(vals)
    
    def upgrade_booking_common(booking, start_date_common, end_date_common, book_start_date, book_end_date):
        for resource in booking:
            # for upgrade booking week
            upgrade_week = booking.env['booking.resource.week'].search([('booking_id', '=', resource.id)])
            day_count = (end_date_common - start_date_common).days
            if len(upgrade_week) > 0:
                upgrade_week.unlink()
            mon_sun = [start_date_common]
            if start_date_common.strftime("%A") == 'Sunday' or\
                 pd.Series(pd.date_range(start_date_common.strftime("%Y-%m-%d"), periods=1)).dt.is_month_end[0] == True:
                mon_sun.append(start_date_common)
            for single_date in (((start_date_common + timedelta(1)) + timedelta(n)) for n in range(day_count)):
                is_start_end_month = pd.Series(pd.date_range(single_date.strftime("%Y-%m-%d"), periods=1))
                if single_date.strftime("%A") == "Monday" or single_date.strftime("%A") == "Sunday":
                    mon_sun.append(single_date)
                if is_start_end_month.dt.is_month_start[0] == True and single_date.strftime("%A") != "Monday" or is_start_end_month.dt.is_month_end[0] == True and int(len(mon_sun))%2 != 0:
                    mon_sun.append(single_date)
            if end_date_common.strftime("%A") != 'Sunday' and pd.Series(pd.date_range(end_date_common.strftime("%Y-%m-%d"), periods=1)).dt.is_month_end[0] != True:
                mon_sun.append(end_date_common)
            if len(mon_sun) % 2 != 0:
                mon_sun.append(end_date_common)
            no_week = 1
            for i in range(0, len(mon_sun), 2):
                message_week={}
                check_effort_rate_week = {}
                resource.booking_upgrade_week.check_effort_week_when_gen(check_effort_rate_week, message_week, mon_sun[i], mon_sun[i+1],\
                    resource.employee_id, resource.effort_rate)
                if check_effort_rate_week['check'] == False:
                    effort_week = resource.effort_rate if resource.effort_rate < message_week['effort_rate'] else message_week['effort_rate']
                else:
                    effort_week = resource.effort_rate
                if mon_sun[i] > book_end_date or mon_sun[i] < book_start_date:
                    effort_week = 0
                week_temp = booking.env['booking.resource.week.temp'].create({
                    'name': 'Week ' + str(no_week),
                    'start_date_week': mon_sun[i],
                    'end_date_week': mon_sun[i+1],
                    'effort_rate_week': effort_week,
                    'booking_id' : resource.id,
                    'employee_id': resource.employee_id.id
                })

                booking.env['booking.resource.week'].create({
                    'name': 'Week ' + str(no_week),
                    'start_date_week': mon_sun[i],
                    'end_date_week': mon_sun[i+1],
                    'effort_rate_week': effort_week,
                    'booking_id' : resource.id,
                    'week_temp_id': week_temp.id,
                    'employee_id': resource.employee_id.id
                })

                no_week += 1


            # for upgrade booking month
            upgrade_month = booking.env['booking.resource.month'].search([('booking_id', '=', resource.id)])
            if len(upgrade_month) > 0:
                upgrade_month.unlink()
            list_start_end = [start_date_common]
            start_date_booking = pd.Series(pd.date_range(start_date_common.strftime("%Y-%m-%d"), periods=1))
            if start_date_booking.dt.is_month_end[0] == True:
                list_start_end.append(start_date_common)
            for date in pd.Series(pd.date_range((start_date_common + timedelta(1)).strftime("%Y-%m-%d"), periods=day_count)):
                if date.is_month_start == True or date.is_month_end == True:
                    list_start_end.append(datetime.strptime(date._date_repr, '%Y-%m-%d').date())
            end_date_booking = pd.Series(pd.date_range(end_date_common.strftime("%Y-%m-%d"), periods=1))
            if end_date_booking.dt.is_month_end[0] == False:
                list_start_end.append(end_date_common)
            for i in range(0, len(list_start_end), 2):
                message_month={}
                check_effort_rate_month = {}
                resource.booking_upgrade_month.check_effort_month_when_gen(check_effort_rate_month, message_month, list_start_end[i], list_start_end[i+1],\
                    resource.employee_id, resource.effort_rate)
                effort_month = resource.compute_effort_month_when_gen(list_start_end[i], list_start_end, resource.employee_id.id,resource.id or resource.id.origin)
                month_temp = booking.env['booking.resource.month.temp'].create({
                    'name': 'Month ' + str(list_start_end[i].month),
                    'start_date_month': list_start_end[i],
                    'end_date_month': list_start_end[i+1],
                    'effort_rate_month': effort_month,
                    'booking_id' : resource.id,
                    'employee_id': resource.employee_id.id
                    })
                
                booking.env['booking.resource.month'].create({
                    'name': 'Month ' + str(list_start_end[i].month),
                    'start_date_month': list_start_end[i],
                    'end_date_month': list_start_end[i+1],
                    'effort_rate_month': effort_month,
                    'booking_id' : resource.id,
                    'month_temp_id': month_temp.id,
                    'employee_id': resource.employee_id.id
                    })
            
            resource.check_upgrade_booking = True
    
    def compute_effort_month_when_gen(self, start_date_month, list_start_end, employee_id, booking_id):
        for _ in range(int(len(list_start_end)/2)):
            total_effort_month = 0
            len_total_week = 0
            for rec in self.env['booking.resource.week'].search([('employee_id', '=', employee_id), ('booking_id', '=', booking_id)]):
                if start_date_month.month == rec.start_date_week.month and start_date_month.year == rec.start_date_week.year:
                    total_effort_month += (rec.effort_rate_week)
                    len_total_week += 1

            if len_total_week > 0:
                return total_effort_month/len_total_week


    def action_upgrade_booking(self):
        booking = self if len(self) > 0 else self.env['planning.calendar.resource'].search([])
        for resource in booking:
            start_date_common = resource.start_date
            end_date_common = resource.end_date
            if pd.Series(pd.date_range(resource.start_date.strftime("%Y-%m-%d"), periods=1)).dt.is_month_start[0] == False:
                start_date_common = date(resource.start_date.year, resource.start_date.month, 1)
            if pd.Series(pd.date_range(resource.end_date.strftime("%Y-%m-%d"), periods=1)).dt.is_month_end[0] == False:
                end_date_common = date(resource.end_date.year, resource.end_date.month, calendar.monthrange(resource.end_date.year, resource.end_date.month)[1])
            
            resource.upgrade_booking_common(start_date_common, end_date_common, resource.start_date, resource.end_date)
            resource.compute_total_effort_common()

    @api.onchange('check_upgrade_booking')
    def _get_booking_resource(self):
        for resource in self:
            resource.booking_upgrade_week = self.env['booking.resource.week'].search([('booking_id', '=', resource.id)])
            resource.booking_upgrade_month = self.env['booking.resource.month'].search([('booking_id', '=', resource.id)])

    @api.onchange('booking_upgrade_week')
    def check_effort_week(self):
        for resource in self:
            if resource.select_type_upgrade == 'week' and resource.inactive==False:
                resource.check_edit_effort = 'effort_week'
                     
    @api.onchange('booking_upgrade_month')
    def check_effort_month(self):
        for resource in self:     
            if resource.select_type_upgrade == 'month' and resource.inactive==False:
                resource.check_edit_effort = 'effort_month'

    def compute_total_effort_common(self):
        for resource in self:
            total_effort_all = 0
            for month in resource.booking_upgrade_month:
                total_effort_all += month.effort_rate_month
            len_booking_update_month = len(resource.env['booking.resource.month'].search([('booking_id', '=', resource.id or resource.id.origin)]))
            if len_booking_update_month > 0:
                self.env['planning.calendar.resource'].search([('id', '=', resource.id or resource.id.origin)]).write({
                    'effort_rate' : total_effort_all / len_booking_update_month
                })
    
    def calculator_total_effort(self):
        self.compute_total_effort_common()

    def calculator_effort_month(self, effort_month_edit, total_effort_week_expired, len_week, len_week_no_expired):
        return ((effort_month_edit * len_week) - (total_effort_week_expired)) / len_week_no_expired

    @api.onchange('effort_rate')
    def update_effort_month(self):
        for resource in self:
            len_week = 0
            len_week_no_expired = 0
            total_effort_week_expired = 0
            actual_end_date = date.today()
            resource.booking_upgrade_month.get_id_month_edit()
            for week in resource.booking_upgrade_week:
                len_week += 1
                if week.start_date_week > date.today():
                    len_week_no_expired += 1 
                else:
                    total_effort_week_expired += week.effort_rate_week

                if week.start_date_week <= date.today() and week.end_date_week >= date.today():
                    actual_end_date = week.end_date_week
            for month in resource.booking_upgrade_month:
                month_total_effort_week_expired = 0
                month_len_week = 0
                month_len_week_no_expired = 0
                for rec_week in resource.booking_upgrade_week:
                    if month.start_date_month.month == rec_week.start_date_week.month and month.start_date_month.year == rec_week.start_date_week.year:
                        month_len_week += 1
                        if rec_week.start_date_week > date.today():
                            month_len_week_no_expired += 1
                        else:
                            month_total_effort_week_expired += rec_week.effort_rate_week                        
                        
                if month.end_date_month > actual_end_date:
                    eft_month = resource.calculator_effort_month(resource.effort_rate, total_effort_week_expired, len_week, len_week_no_expired)
                    if (month_len_week - month_len_week_no_expired) == 0:
                        month.effort_rate_month = eft_month
                    else:
                        month.effort_rate_month = (month_total_effort_week_expired + eft_month*month_len_week_no_expired)/month_len_week              

    @api.constrains('booking_upgrade_week', 'booking_upgrade_month')
    def recompute_when_save(self):
        for resource in self:
            if resource.booking_upgrade_week and resource.booking_upgrade_month:
                resource.compute_total_effort_common()  

                
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
