from odoo import fields, models, tools

class ProjectManagementTotal(models.Model):
    _name = 'project.management.total'
    _auto = False
    
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    project_cost = fields.Float(string="Project Cost")
    profit = fields.Float(string="Profit")
    salary = fields.Float(string="Salary Cost")
    members = fields.Float(string='Members')
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT pmh.project_management_id,
                    SUM(pmh.members) AS count_members,
                    SUM (pmh.total_project_expense) AS project_cost,
                    SUM (pmh.profit) AS profit,
                    SUM (pmh.total_salary) AS total_salary
                FROM project_management_history AS pmh
                GROUP BY
                    pmh.project_management_id 
            )""" % (self._table)
        )