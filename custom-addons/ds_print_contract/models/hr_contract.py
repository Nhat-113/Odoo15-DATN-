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

    def format_time(self):
        morning_shift = next((att for att in self.resource_calendar_id.attendance_ids if att.day_period == "morning"), False)
        afternoon_shift = next((att for att in self.resource_calendar_id.attendance_ids if att.day_period == "afternoon"), False)
        data = {
                "hour_from_morning": "8h00",
                "hour_to_morning": "12h00",
                "hour_from_afternoon": "13h30",
                "hour_to_afternoon": "17h30",
        }
        if morning_shift and afternoon_shift:
            data['hour_from_morning'] = morning_shift.hour_from
            data['hour_to_morning'] = morning_shift.hour_to
            data['hour_from_afternoon'] = afternoon_shift.hour_from
            data['hour_to_afternoon'] = afternoon_shift.hour_to

            for key, value in data.items():
                hours = int(value)
                minutes = int((value - hours) * 60)
                data[key] = f"{hours:2}h{minutes:02}"
        return data

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
            if self.contract_document_type == 'collaborator':
                template = self.env.ref(
                    'ds_print_contract.collaborator_contract_mail_template', False)
            if self.contract_document_type == 'annex':
                template = self.env.ref(
                    'ds_print_contract.annex_contract_mail_template', False)
            if self.contract_document_type == 'offical_labor' and self.struct_id.id == 2:
                template = self.env.ref(
                    'ds_print_contract.offical_labor_contract_gross_mail_template', False)
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

    # ------------------------------------------------------
    # FOLLOWERS API
    # ------------------------------------------------------
    
    # @Override
    # Disable the feature of automatically adding the manager department to followers when changing the department from the hr.contract model
    def _message_auto_subscribe(self, updated_values, followers_existing_policy='skip'):
        return True
