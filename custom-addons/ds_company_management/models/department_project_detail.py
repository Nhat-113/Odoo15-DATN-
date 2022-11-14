from odoo import fields, models, tools


class DepartmentProjectDetail(models.Model):
    _name = 'department.project.detail'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                    pmh.project_id,
                    pmh.company_id,
                    pm.user_pm,
                    (CONCAT((EXTRACT(YEAR FROM pmh.month_start))::text, ' ', TO_CHAR(pmh.month_start, 'Month'))) AS months,
                    pmh.months_domain,
                    pmh.month_start,
                    pmh.month_end,
                    pmh.working_day,
                    pmh.total_project_expense AS total_project_cost,
                    pmh.members AS total_members,
                    pmh.total_salary,
                    pmh.revenue AS total_revenue,
                    pmh.total_commission,
                    pmh.total_avg_operation_project,
                    pmh.profit AS total_profit,
                    pmh.profit_margin,
                    pmh.currency_id,
                    pm.department_id,
                    pmh.project_management_id

                FROM project_management_history AS pmh
                LEFT JOIN project_management AS pm
                    ON pm.id = pmh.project_management_id
                
            ) """ % (self._table)
        )
        
        
    
class DepartmentProjectDetailData(models.Model):
    _name = 'department.project.detail.data'

        
    project_management_id = fields.Many2one('project.management.data', string="Project Management")
    company_id = fields.Many2one('res.company', string='Company')
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one('hr.department', string='Department')
    user_pm = fields.Many2one('res.users', string="PM")
    currency_id = fields.Many2one('res.currency', string="Currency")
    months = fields.Char(string="Month")
    months_domain = fields.Date(string="Month domain")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    working_day = fields.Float(string="Working Day")
    total_members = fields.Float(string='Effort(MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_project_cost = fields.Float(string="Prj Expenses")
    total_revenue = fields.Float(string="Revenue")
    total_avg_operation_project = fields.Float(string="Total Avg Operation Project")
    total_commission = fields.Float(string="Commission")
    total_profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2), help="Profit Margin = profit / revenue * 100")
    
    
    def get_detail_project_management(self):
        action = {
            # 'name': self.project_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management.data',
            'res_id': self.project_management_id.id,
            'view_ids': self.env.ref('ds_company_management.view_form_project_management').id,
            'view_mode': 'form'
        }
        return action