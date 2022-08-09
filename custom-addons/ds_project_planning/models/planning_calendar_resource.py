# -*- coding: utf-8 -*-
import pandas as pd

from calendar import calendar
from email.policy import default
from attr import field
from numpy import require
from odoo import models, fields, api, _
from datetime import date, datetime, time
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
    duration = fields.Integer(compute='_compute_duration', string="Duration",
                              readonly=True, help="The duration of working time in the project", default=1)
    calendar_effort = fields.Float(string="Booking Effort", default=0, compute='_compute_calendar_effort', readonly=True)
    effort_rate = fields.Float(string="Effort Rate", compute='_compute_effort_rate_default',readonly=False,
                               help="Effort Rate (%) = Booking Effort * 20 / Duration", store=True, default=0)
    role_ids = fields.Many2many('planning.roles', string='Roles')
    note = fields.Text(string='Note')
    member_type = fields.Many2one(
        'planning.member.type', string="Member Type")
    member_type_rate = fields.Float(
        related='member_type.rate', string="Member Type (%)")
    inactive = fields.Boolean(string="Inactive Member",
                              default=False, store=True)
    inactive_date = fields.Date(string='Inactive Date', help="The start date of the member's inactivity in the project.",
                                default=fields.Date.today)

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

    @api.onchange('inactive')
    def _set_inactive_date(self):
        if self.inactive == False:
            self.inactive_date = False

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
                message['effort_rate'] = (100 - total_effort_booked) if (100 - total_effort_booked) > 0 else 0
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

        return super(PlanningCalendarResource, self).unlink()

    def write(self, vals):
        for calendar in self:
            if calendar.end_date < date.today() and calendar.env.user.has_group('project.group_project_manager') == False:
                raise UserError(_(
                        'Can not edit member (%(resource)s) with End Date (%(end)s) < Current Date (%(current)s).',
                        resource=calendar.employee_id.name, end=calendar.end_date, current=date.today()
                    ))

        return super(PlanningCalendarResource, self).write(vals)


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
