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

class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'
