# -*- coding:utf-8 -*-

from odoo import api, fields, models


class ContractReport(models.AbstractModel):
    _name = 'report.ds_print_contract.contract_qweb_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        contract_info = self.env['hr.contract'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contract_info,
            'data': data,
        }


class ProbationaryContractReport(models.AbstractModel):
    _name = 'report.ds_print_contract.probationary_contract_qweb_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        contract_info = self.env['hr.contract'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contract',
            'docs': contract_info,
            'data': data,
        }


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    duration_months = fields.Integer(string="Duration",
                                     default=2)

    def send_email_contract(self):
        """
        This function opens a window to compose an email, with the edi payslip template message loaded by default
        """
        self.ensure_one()
        try:
            # defaut template: "offical_labor"
            template = self.env.ref(
                    'ds_print_contract.offical_labor_contract_mail_template', False)

            if self.contract_document_type == 'probationary':
                template = self.env.ref(
                    'ds_print_contract.probationary_contract_mail_template', False)
            if self.contract_document_type == 'internship':
                template = self.env.ref(
                    'ds_print_contract.internship_contract_mail_template', False)
        except ValueError:
            template = False
        try:
            compose_form_id = self.env.ref(
                'mail.email_compose_message_wizard_form').id
        except ValueError:
            compose_form_id = False
        ctx = dict(
            default_model='hr.contract',
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
