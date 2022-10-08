from odoo import api, fields, models, _

class Project(models.Model):
    _inherit = 'project.project'


    def _compute_expenses_company_count(self):
        count = self.env['project.expense.management'].search_count([('project_id', '=', self.id)])
        for record in self:
            record.expenses_company_count = count  

    expenses_company_count = fields.Integer('# Expenses', compute=_compute_expenses_company_count, groups='ds_expense_management.administrator_access_company_expense')
    
    
    def action_open_project_company_expenses(self):
        action = self.env["ir.actions.actions"]._for_xml_id("ds_expense_management.project_expense_management_action")
        action.update({
            'display_name': _('Expenses'),
            'views': [[False, 'tree'], [False, 'form'], [False, 'kanban'], [False, 'graph'], [False, 'pivot']],
            'context': {'default_company_id': self.company_id.id, 'default_project_id': self.id},
            'domain': [('company_id', '=', self.company_id.id), ('project_id', '=', self.id)]
        })
        return action