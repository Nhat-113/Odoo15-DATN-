from odoo import models, api,_

class HrEmployee(models.Model):
    _inherit = "hr.employee"

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

        if is_checkin == 'True':
            vals = {
                'employee_id': self.id,
                'check_in': action_date,
            }
            return self.env['hr.attendance'].create(vals) 
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