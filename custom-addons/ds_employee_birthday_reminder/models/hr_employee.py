from datetime import datetime, timedelta, date
from email.policy import default

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def get_employee_birthday_info(self):
        reminder_before_day = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("employee.reminder_before_day")
        )
        next_date = datetime.today() + timedelta(days=int(reminder_before_day or 1))
        employee_ids = self.env["hr.employee"].search(
            [
                ("birthday_date", "=", next_date.day),
                ("birthday_month", "=", next_date.month),
            ]
        )
        return {
            "employees": employee_ids,
            "date": next_date.strftime(DEFAULT_SERVER_DATE_FORMAT),
        }


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _default_age_with_employee(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            if employee.birthday:
                today = date.today()
                age = today.year - employee.birthday.year - (
                    (today.month, today.day) < (employee.birthday.month, employee.birthday.day))
                employee.employee_age = str(age)  
        

    birthday_date = fields.Integer(compute="_compute_get_birthday_identifier", store=1)
    birthday_month = fields.Integer(compute="_compute_get_birthday_identifier", store=1)
    employee_age = fields.Char(string="Age", default=_default_age_with_employee)

    @api.depends("birthday")
    def _compute_get_birthday_identifier(self):
        for employee in self.filtered(lambda e: e.birthday):
            employee.birthday_date = employee.birthday.day
            employee.birthday_month = employee.birthday.month

    @api.onchange('birthday')
    def onchange_employee_birthday(self):
        if self.birthday:
            today = date.today()
            age = today.year - self.birthday.year - (
                (today.month, today.day) < (self.birthday.month, self.birthday.day))
            self.employee_age = str(age)

    @api.model
    def send_birthday_reminder_employee(self):
        IrConfigParameter = self.env["ir.config_parameter"].sudo()
        template_env = self.env["mail.template"]
        send_employee = bool(IrConfigParameter.get_param("employee.send_wish_employee"))
        send_manager = bool(IrConfigParameter.get_param("employee.send_wish_manager"))

        # Send birthday wish to employee
        if send_employee:
            domain = [
                ("birthday_date", "=", datetime.today().day),
                ("birthday_month", "=", datetime.today().month),
            ]
            emp_template_id = IrConfigParameter.get_param(
                "employee.emp_wish_template_id"
            )
            if emp_template_id:
                template_id = template_env.sudo().browse(int(emp_template_id))
                for employee in self.env["hr.employee"].search(domain):
                    template_id.send_mail(employee.id)

        # Send birthday reminder to HR manager
        if send_manager:
            birthday_info = self.env["res.users"].get_employee_birthday_info()
            if len(birthday_info.get("employees")):
                manager_template_id = IrConfigParameter.get_param(
                    "employee.manager_wish_template_id"
                )
                if manager_template_id:
                    template_id = template_env.sudo().browse(int(manager_template_id))
                    for manager in self.env.ref("hr.group_hr_manager").users:
                        template_id.send_mail(manager.id)

    def send_birthday(self):
            """
            This function opens a window to compose an email, with the edi payslip template message loaded by default
            """
            self.ensure_one()
            try:
                template = self.env.ref(
                    'ds_employee_birthday_reminder.email_birthday_wishes_employee_template', False)
            except ValueError:
                template = False

            if self.id != self.env.user.employee_id.id:
                try:
                    compose_form_id = self.env.ref(
                        'mail.email_compose_message_wizard_form').id
                except ValueError:
                    compose_form_id = False
                ctx = dict(
                    default_model='hr.employee',
                    default_res_id=self.id,
                    default_use_template=bool(template),
                    default_template_id=template and template.id or False,
                    default_composition_mode='comment',
                )
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'mail.compose.message',
                    'views': [(compose_form_id, 'form')],
                    'view_id': compose_form_id,
                    'target': 'new',
                    'context': ctx,
                }