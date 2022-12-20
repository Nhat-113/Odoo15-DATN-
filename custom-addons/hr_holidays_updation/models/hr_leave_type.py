from email.policy import default
from odoo import models, fields
from datetime import date


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    company_id = fields.Many2one('res.company', string='Company', default=False)

    def gen_cron_job_reserved_leave(self):
        year = int(self.env['ir.config_parameter'].search([('key', '=', 'time_off_reserve')]).value)
        for employee in self.env['hr.employee'].search([('active', '=', True)]):
            time_off_id = self.env['hr.leave.type'].search([('company_id', '=', employee.company_id.id), ('name', 'like', 'Nghỉ phép có lương')]).id
            number_of_day = employee.time_off_remaining
            # 3 is the maximum number of vacation days reserved 
            if employee.time_off_remaining > 3:
                number_of_day = 3

            if time_off_id != False and number_of_day > 0:
                self.env['hr.leave.allocation'].create({
                    'name': 'Nghỉ phép bảo lưu của năm ' + str(year - 1),
                    'holiday_status_id': time_off_id,
                    'holiday_type': 'employee',
                    'employee_id': employee.id,
                    'date_from': date(year, 1, 1), 
                    'date_to': date(year, 3, 31),
                    'number_of_days': number_of_day, 
                    'number_of_days_display': number_of_day,
                    'notes': False,
                    'state': 'validate',
                    'multi_employee': False, 
                })

        self.env['ir.config_parameter'].search([('key', '=', 'time_off_reserve')]).write({
            'value': year + 1
        })

    def gen_cron_job_time_off(self):
        year = int(self.env['ir.config_parameter'].search([('key', '=', 'time_off_every_year')]).value)
        for employee in self.env['hr.employee'].search([('active', '=', True)]):
            time_off_id = self.env['hr.leave.type'].search([('company_id', '=', employee.company_id.id), ('name', 'like', 'Nghỉ phép có lương')]).id

            if employee.company_id.id == 1:
                company_name = "DSOFT_"
            elif employee.company_id.id == 2:
                company_name = "MIRAI_"
            elif employee.company_id.id == 3:
                company_name = "MTECH_"
            else:
                company_name = ''

            # 12 is a paid leave day
            number_of_day = 12
            if time_off_id:
                self.env['hr.leave.allocation'].create({
                    'name': company_name + 'Nghỉ phép có lương',
                    'holiday_status_id': time_off_id,
                    'holiday_type': 'employee',
                    'employee_id': employee.id,
                    'date_from': date(year, 1, 1), 
                    'date_to': date(year, 12, 31),
                    'number_of_days': number_of_day, 
                    'number_of_days_display': number_of_day,
                    'notes': False,
                    'state': 'validate',
                    'multi_employee': False, 
                })

        self.env['ir.config_parameter'].search([('key', '=', 'time_off_every_year')]).write({
            'value': year + 1
        })
