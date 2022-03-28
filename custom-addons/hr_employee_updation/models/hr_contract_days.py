
from odoo import models, fields, api, _
from datetime import timedelta, datetime


class HrEmployeeContract(models.Model):
    _inherit = 'hr.contract'

    def _get_default_notice_days(self):
        if self.env['ir.config_parameter'].get_param(
                'hr_resignation.notice_period'):
            return self.env['ir.config_parameter'].get_param(
                'hr_resignation.no_of_days')
        else:
            return 0

    notice_days = fields.Integer(string="Notice Period",
                                 default=_get_default_notice_days)

    @api.model
    def mail_contract_reminder(self):
        """Sending contract end date notification for Contract before 'notice_days'"""
        contract_ids = self.env["hr.contract"].search(
            [
                ("state", "=", "open"),
            ]
        )
        current_date = fields.Date.context_today(self) + timedelta(days=1)
        for contract in contract_ids:
            reminder_before_day = contract.notice_days
            exp_date = fields.Date.from_string(
                datetime.today()) + timedelta(days=int(reminder_before_day or 7))
            contract_end_date = fields.Date.from_string(contract.date_end)

            if contract_end_date == exp_date:
                """Send email notification to HR"""
                for manager in self.env.ref("hr.group_hr_manager").users:
                    mail_content = "  Hello  " + manager.name + ",<br> The Contract of employee " + "<b>" + contract.employee_id.name + "</b>" + " with name " + contract.name + "is going to <b> expire on </b> " + \
                        str(contract.date_end) + \
                        ". Please renew contract before expiry date."
                    main_content = {
                        'subject': _('Contract-%s Expired On %s') % (
                            contract.name, contract.date_end),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': manager.work_email,
                    }
                    self.env['mail.mail'].sudo().create(
                        main_content).send()

                """Send email notification to employee"""
                mail_content_emp = "  Hello  " + contract.employee_id.name + ",<br> Your current Contract with name " + "<b>" + contract.name + "</b>" + " is going to <b> expire on </b>" + \
                    "<b>" + str(contract.date_end) + "</b>" + \
                    ". If you have any questions, do not hesitate to contact HR."
                main_content_emp = {
                    'subject': _('Contract-%s Expired On %s') % (
                        contract.name, contract.date_end),
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content_emp,
                    'email_to': contract.employee_id.work_email,
                }
                self.env['mail.mail'].sudo().create(
                    main_content_emp).send()
