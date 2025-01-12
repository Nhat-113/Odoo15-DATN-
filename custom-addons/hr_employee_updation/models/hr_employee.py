# -*- coding: utf-8 -*-
################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Hajaj Roshan(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from datetime import timedelta
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee",
                                  help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation",
                                  help="Relationship with the employee")
    member_name = fields.Char(string='Name')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)

    
class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        current_date = fields.Date.context_today(self) + timedelta(days=1)
        employee_ids = self.search(['|', ('id_expiry_date', '!=', False),
                                    ('passport_expiry_date', '!=', False)])
        for emp in employee_ids:
            if emp.id_expiry_date:
                exp_date = fields.Date.from_string(
                    emp.id_expiry_date) - timedelta(days=14)
                if current_date >= exp_date:
                    mail_content = "  Hello  " + emp.name + ",<br>Your ID " + emp.identification_id + "is going to expire on " + \
                                   str(emp.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (
                            emp.identification_id, emp.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emp.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
            if emp.passport_expiry_date:
                exp_date = fields.Date.from_string(
                    emp.passport_expiry_date) - timedelta(days=180)
                if current_date >= exp_date:
                    mail_content = "  Hello  " + emp.name + ",<br>Your Passport " + emp.passport_id + "is going to expire on " + \
                                   str(emp.passport_expiry_date) + ". Please renew it before expire"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (
                            emp.passport_id, emp.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': emp.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    personal_mobile = fields.Char(
        string='Mobile',
        related='address_home_id.mobile', store=True,
        help="Personal mobile number of the employee")
    joining_date = fields.Date(
        string='Joining Date',
        help="Employee joining date computed from the contract start date",
        compute='_compute_joining_date', store=True)
    identification_place = fields.Char(
        string='Identification Place', store=True,
        help="Employee identification cards are created in this location")
    id_start_date = fields.Date(
        string='Start Date',
        help='Start date of Identification ID')
    id_expiry_date = fields.Date(
        string='Expiry Date',
        help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(
        string='Expiry Date',
        help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many(
        'ir.attachment', 'id_attachment_rel',
        'id_ref', 'attach_ref',
        string="Attachment",
        help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many(
        'ir.attachment',
        'passport_attachment_rel',
        'passport_ref', 'attach_ref1',
        string="Attachment",
        help='You can attach the copy of Passport')
    fam_ids = fields.One2many(
        'hr.employee.family', 'employee_id',
        string='Family', help='Family Information')
    insurance_id = fields.Char(string='Insurance ID', groups="hr.group_hr_user",  tracking=True)
    personal_income_tax_code = fields.Char(string="Personal Income Tax Code", groups="hr.group_hr_user", tracking=True)
    address = fields.Char(string='Address', groups="hr.group_hr_user",  tracking=True)
    time_off_remaining = fields.Float('Remaining TimeOff', compute='get_time_off_remaining')

    @api.depends_context('employee_id', 'default_employee_id')
    def get_time_off_remaining(self):
        for employee in self:

            data_days = (self.get_employees_days(employee.id)[employee.id[0]] if isinstance(employee.id, list) else
                         self.get_employees_days([employee.id])[employee.id])

            employee.time_off_remaining = data_days.get('time_off_remaining')

    def get_employees_days(self, employee_ids, date=None):
        result = {
            employee_id: {
                    'time_off_remaining': 0
            } for employee_id in employee_ids
        }

        if not date:
            date = fields.Date.context_today(self)

        all_allocations = self.env['hr.leave.allocation'].search([
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('date_from', '<=', date),
            '|', ('date_to', '=', False),
                 ('date_to', '>=', date),
        ])

        id_holiday = []
        for all_allocation in all_allocations:
            if all_allocation.holiday_status_id.id not in id_holiday:
                id_holiday.append(all_allocation.holiday_status_id.id)


        requests = self.env['hr.leave'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', id_holiday)
        ])

        allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', id_holiday),
            ('date_from', '<=', date),
            '|', ('date_to', '=', False),
                 ('date_to', '>=', date),
        ])

        for request in requests:
            status_dict = result[request.employee_id.id]
            if not request.holiday_allocation_id or request.holiday_allocation_id in allocations:
                if request.leave_type_request_unit == 'hour':
                    status_dict['time_off_remaining'] -= request.number_of_hours_display/8
                else:
                    status_dict['time_off_remaining'] -= request.number_of_days

        for allocation in allocations.sudo():
            status_dict = result[allocation.employee_id.id]
            if allocation.state == 'validate':
                if allocation.type_request_unit == 'hour':
                    status_dict['time_off_remaining'] += allocation.number_of_hours_display/8
                else:
                    status_dict['time_off_remaining'] += allocation.number_of_days
        return result

    def _first_contract(self):
        hr_contract = self.env['hr.contract'].sudo()
        return hr_contract.search([('employee_id', '=', self.id)],
                                  order='date_start asc', limit=1)

    @api.depends('contract_id')
    def _compute_joining_date(self):
        for rec in self:
            first_contract = rec._first_contract()
            rec.joining_date = min(first_contract.mapped('date_start'))\
                if first_contract else False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        if self.spouse_complete_name and self.spouse_birthdate:
            self.fam_ids = [(0, 0, {
                'member_name': self.spouse_complete_name,
                'relation_id': relation.id,
                'birth_date': self.spouse_birthdate,
            })]

    @api.constrains('work_email')
    def _check_work_email(self):
        work_emails = [employee.work_email for employee in self.env['hr.employee'].search([('id', '!=', self.id)])]
        for employee in self:
            if employee.work_email == False:
               raise UserError('Work email cannot be left blank')
            else:
                if (employee.work_email in work_emails):
                    raise ValidationError(_("Work email is already in use."))


class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'

    name = fields.Char(string="Relationship",
                       help="Relationship with thw employee")
