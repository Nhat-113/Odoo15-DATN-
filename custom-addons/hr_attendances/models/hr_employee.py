from odoo import models, api, fields,_
from dateutil import tz
import zmq
import time
import psutil
from odoo.tools import config
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    fingerprint_template = fields.Char(string='Fingerprint', required=False)
    attendance_ids = fields.One2many(
        'hr.attendance', 'employee_id', groups="hr_attendance.group_hr_attendance_user",
        help='list of attendances for the employee', store=False)
    last_attendance_id = fields.Many2one(
        'hr.attendance', compute='_compute_last_attendance_id', store=False,
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance")
    last_check_in = fields.Datetime(
        related='last_attendance_id.check_in', store=False,
        groups="hr_attendance.group_hr_attendance_user")
    last_check_out = fields.Datetime(
        related='last_attendance_id.check_out', store=False,
        groups="hr_attendance.group_hr_attendance_user")
    attendance_state = fields.Selection(
        string="Attendance Status", compute='_compute_attendance_state',
        selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")],
        groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance")
    sync_write_date = fields.Datetime(string="Sync Field Date", compute='check_sync', store=True,)

    @api.depends('name', 'work_email', 'image_1920', 'fingerprint_template', 'active')
    def check_sync(self):
        current_date = fields.Datetime.now()
        for rec in self:
            rec.sync_write_date = current_date

    def unlink(self):
        for record in self:
            record.active = False
            record.departure_date = fields.Date.today()
            
        contract_records = self.env['hr.contract'].search([
            ('employee_id', 'in', self.ids),
            ('state', '=', 'open')
        ])
        for contract in contract_records:
            contract.write({'date_end': fields.Date.today()})


    def attendance_manual_api(self, employee, date_time, next_action, is_checkin, entered_pin=None):
        employee.ensure_one()
        can_check_without_pin = not employee.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == employee.sudo().pin:
            return employee._attendance_action_api(next_action, date_time, is_checkin)
        return {'warning': _('Wrong PIN')}


    def _attendance_action_api(self, next_action, date_time, is_checkin):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        self.ensure_one()
        employee = self.sudo()
        action_message = self.env["ir.actions.actions"]._for_xml_id("hr_attendance.hr_attendance_action_greeting_message")
        action_message['previous_attendance_change_date'] = employee.last_attendance_id and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today

        if employee.user_id:
            modified_attendance = employee.with_user(employee.user_id)._attendance_action_change_api(date_time, is_checkin)
        else:
            modified_attendance = employee._attendance_action_change_api(date_time, is_checkin)
        action_message['attendance'] = modified_attendance.read()[0]
        action_message['total_overtime'] = employee.total_overtime

        return {'action': action_message}

    def _attendance_action_change_api(self, date_time, is_checkin):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = date_time
        local_tz = tz.gettz('Asia/Ho_Chi_Minh')
        date_convert = action_date.replace(tzinfo=tz.UTC).astimezone(local_tz).date()

        if is_checkin == 'True':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            domain = [('employee_id', '=', self.id), ('start', '=', date_convert)]
            model_attendance = self.env['hr.attendance']
            model_pesudo = self.env['hr.attendance.pesudo']
            is_exists = model_attendance.search(domain)
            if is_exists:
                pesudo = model_pesudo.search(domain)
                if pesudo:
                    pesudo.write({'check_out': action_date})
                    return pesudo
                else:
                    return model_pesudo.create({'employee_id': self.id, 'check_in': is_exists.check_in, 'check_out': action_date})
            else:
                model_attendance.create(vals)
                vals['check_out'] = action_date
                return model_pesudo.create(vals)
        else:
            try:
                last_record_id = max(self.env['hr.attendance'].search([('employee_id', '=', self.id)]).ids)
            except:
                last_record_id = None
            attendance_after = self.env['hr.attendance'].search([('employee_id', '=', self.id),('id','=', last_record_id)])
            if attendance_after.check_in and attendance_after.check_out==False:
                attendance_after.check_out = action_date
                return attendance_after
            else:
                vals = {
                    'check_in': False,
                    'employee_id': self.id,
                    'check_out': action_date,
                }
                return self.env['hr.attendance'].create(vals)
            

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for employee in self:
            try:
                try:
                    last_record_id = max(self.env['hr.attendance'].search([('employee_id', '=', self.id)]).ids)
                except:
                    last_record_id = None
                employee.last_attendance_id = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),('id','=',last_record_id)
                ])
            except:
                employee.last_attendance_id = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                ], limit=1)
                


    # #################################
    # Override function to block URL Check In / Out manual for user
    # #################################
    def attendance_manual(self, next_action, entered_pin=None):
        if self.env.user.has_group('hr_attendance.group_hr_attendance_user') == False:
            raise UserError (_('You cannot access the Check In / Out manual! Please use the Facelog device to Check In / Out and do not access this URL'))
        self.ensure_one()
        can_check_without_pin = not self.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (
                    self.user_id == self.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self._attendance_action(next_action)
        return {'warning': _('Wrong PIN')}
    
    # #################################
    # This all functions update from newest source
    # #################################

    @api.constrains('work_email')
    def _check_work_email(self):
        for employee in self:
            if employee.work_email == False:
               raise UserError('Work email cannot be left blank')
            else:
                if self.env['hr.employee'].sudo().search_count([('work_email', '=', employee.work_email)]) > 1:
                    raise ValidationError(_("Work email is already in use."))

class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    fingerprint_template = fields.Char(string='Fingerprint', required=False, related="employee_id.fingerprint_template", groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance")
    sync_write_date = fields.Datetime(string="Sync Field Date", required=False, related="employee_id.sync_write_date", groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance")