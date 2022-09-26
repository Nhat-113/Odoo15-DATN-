from odoo import fields, models, tools


class DepartmentProjectDetail(models.Model):
    _name = 'department.project.detail'
    _auto = False
    
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    company_id = fields.Many2one('res.company', string='Company')
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one('hr.department', string='Department')
    user_pm = fields.Many2one('res.users', string="Project Manager")
    currency_id = fields.Many2one('res.currency', string="Currency")
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    working_day = fields.Float(string="Working Day")
    total_members = fields.Float(string='Members')
    total_salary = fields.Monetary(string="Salary Cost")
    total_project_cost = fields.Monetary(string="Project Cost")
    total_revenue = fields.Monetary(string="Revenue")
    total_profit = fields.Monetary(string="Profit")
    
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                    pmh.project_id,
                    pmh.company_id,
                    pm.user_pm,
                    pmh.month_start,
                    pmh.month_end,
                    pmh.working_day,
                    pmh.total_project_expense AS total_project_cost,
                    pmh.members AS total_members,
                    pmh.total_salary,
                    pmh.revenue AS total_revenue,
                    pmh.profit AS total_profit,
                    pmh.currency_id,
                    pm.department_id,
                    pmh.project_management_id

                FROM project_management_history AS pmh
                LEFT JOIN project_management AS pm
                    ON pm.id = pmh.project_management_id
                
            ) """ % (self._table)
        )
        
        
    
    def get_detail_project_management(self):
        action = {
            # 'name': self.project_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management',
            'res_id': self.project_management_id.id,
            'view_ids': self.env.ref('ds_company_management.view_form_project_management').id,
            'view_mode': 'form'
        }
        return action