from email.policy import default
from odoo import models, fields
from datetime import date
from odoo.exceptions import UserError

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    company_id = fields.Many2one('res.company', string='Company', default=False)

    def gen_cron_job_reserved_leave(self):
        try:
            current_year = date.today().year
            next_year = current_year + 1
            # 3 is the maximum number of vacation days reserved
            max_days_reserved = 3

            active_employees = self.env['hr.employee'].search([('active', '=', True)])
            for employee in active_employees:
                domain = [
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', date(next_year, 1, 1)),
                    ('date_to', '<=', date(next_year, 12, 31))
                ]
                group_record = self.env["hr.leave"].read_group(
                    domain = domain, 
                    fields = ['holiday_status_id', 'number_of_days:sum'], 
                    groupby = ['holiday_status_id'])
                
                used_day_next_year = sum(group['number_of_days'] for group in group_record) if group_record else 0

                time_off_id = self.env['hr.leave.type'].search([('company_id', '=', employee.company_id.id), ('name', 'like', 'Nghỉ phép có lương')]).id
                date_to = date(next_year, 3, 31)
                
                # time_off_remaining is the number of time off left in current year
                number_of_days = min(employee.time_off_remaining, max_days_reserved)
                    
                if used_day_next_year <= number_of_days:
                    number_of_days = number_of_days - used_day_next_year
                else:
                    date_to = date(next_year, 12, 31)

                if time_off_id and number_of_days > 0:
                    self.env['hr.leave.allocation'].create({
                        'name': 'Nghỉ phép bảo lưu của năm ' + str(current_year),
                        'holiday_status_id': time_off_id,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'date_from': date(next_year, 1, 1),
                        'date_to': date_to,
                        'number_of_days': number_of_days, 
                        'number_of_days_display': number_of_days,
                        'notes': False,
                        'state': 'validate',
                        'multi_employee': False, 
                    })
        except Exception as e:
            raise UserError(e)
            

    def gen_cron_job_time_off(self):
        try:
            current_year = date.today().year
            next_year = current_year + 1
            
            active_employees = self.env['hr.employee'].search([('active', '=', True)])
            for employee in active_employees:
                time_off_id = self.env['hr.leave.type'].search([('company_id', '=', employee.company_id.id), ('name', 'like', 'Nghỉ phép có lương')]).id
                if time_off_id:
                    company_name = employee.company_id.name

                    # 12 is a paid leave day
                    number_of_day = 12
                    self.env['hr.leave.allocation'].create({
                        'name': company_name + '_Nghỉ phép có lương_' + str(next_year),
                        'holiday_status_id': time_off_id,
                        'holiday_type': 'employee',
                        'employee_id': employee.id,
                        'date_from': date(next_year, 1, 1), 
                        'date_to': date(next_year, 12, 31),
                        'number_of_days': number_of_day, 
                        'number_of_days_display': number_of_day,
                        'notes': False,
                        'state': 'validate',
                        'multi_employee': False, 
                    })
        except Exception as e:
                raise UserError(e)
