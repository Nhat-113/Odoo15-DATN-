# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    def _domain_project_id(self):
        domain = [('allow_timesheets', '=', True)]
        return domain

    project_id = fields.Many2one(
        'project.project', 'Project', compute='_compute_project_id', store=True, readonly=False,
        domain=_domain_project_id)    
            
    @api.model
    def default_get(self, field_list):
        result = super(AccountAnalyticLine, self).default_get(field_list)
        if 'encoding_uom_id' in field_list:
            result['encoding_uom_id'] = self.env.company.timesheet_encode_uom_id.id
        if not self.env.context.get('default_employee_id') and 'employee_id' in field_list and result.get('user_id'):
            result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', result['user_id'])], limit=1).id
       
        return result
        