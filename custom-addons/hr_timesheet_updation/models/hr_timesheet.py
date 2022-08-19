# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, AccessError
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

    @api.constrains('project_id', 'task_id')
    def _check_task_in_project(self):
        for timesheet in self:
            if timesheet.task_id.project_id.id != timesheet.project_id.id:
                raise UserError(_('The task "%(task)s" is not belong to the project "%(project)s".', project=timesheet.project_id.name, task=timesheet.task_id.name))
                

        