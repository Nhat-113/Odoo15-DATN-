from odoo import models, fields, api, exceptions, _
from odoo.tools import float_round


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def attendance_manual_api(self, employee, date_time, next_action):
        employee.ensure_one()
        can_check_without_pin = not employee.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (employee.user_id == employee.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == employee.sudo().pin:
            return employee._attendance_action_api(next_action, date_time)
        return {'warning': _('Wrong PIN')}


    def _attendance_action_api(self, next_action, date_time):
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
            modified_attendance = employee.with_user(employee.user_id)._attendance_action_change_api(date_time)
        else:
            modified_attendance = employee._attendance_action_change_api(date_time)
        action_message['attendance'] = modified_attendance.read()[0]
        action_message['total_overtime'] = employee.total_overtime

        return {'action': action_message}

    def _attendance_action_change_api(self, date_time):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = date_time

        if self.attendance_state != 'checked_in':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id), ('check_out', '=', False)], limit=1)
        if attendance:
            attendance.check_out = action_date
        else:
            raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance