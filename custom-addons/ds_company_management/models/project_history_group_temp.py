from odoo import fields, models, tools


class ProjectHistoryGroup(models.Model):
    _name = 'project.history.group.temp'
    _auto = False
    _description = 'Model support calculate total fields from Cost Management'
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    company_id = fields.Many2one('res.company', string="Company")
    project_id = fields.Many2one('project.project', string="Project")
    total_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_profit = fields.Float(string="Profit")
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    project_id AS id,
                    project_id,
                    SUM(members) AS total_members,
                    SUM(total_salary) AS total_salary,
                    SUM(total_project_expense) AS total_project_expense,
                    SUM(total_department_expense) AS total_department_expense,
                    SUM(profit) AS total_profit,
                    SUM(total_avg_operation_project) AS total_avg_operation_project

                FROM project_management_history
                GROUP BY project_id
            ) """ % (self._table)
        )