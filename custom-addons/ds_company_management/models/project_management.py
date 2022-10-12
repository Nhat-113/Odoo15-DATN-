from odoo import fields, models, tools


class ProjectManagement(models.Model):
    _name = "project.management"
    _description = "Project Management"
    _auto = False
    _rec_name = "project_id"
    

    def _content_compute_total(self):
        for record in self:
            record.count_members = sum(item.members for item in record.project_management_history)
            record.total_salary = sum(item.total_salary for item in record.project_management_history)
            record.profit = sum(item.profit for item in record.project_management_history)
            record.last_update_color = record.project_id.last_update_color
        

    id = fields.Integer("ID")
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one("hr.department", string="Department")
    user_pm = fields.Many2one('res.users', string="Project Manager")
    company_id = fields.Many2one('res.company', string="Company")
    currency_id = fields.Many2one('res.currency', string="Currency")
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    status = fields.Char(string='Status')
    
    # bonus = fields.Float(string="Bonus")
    revenue = fields.Monetary(string="Revenue")
    project_cost = fields.Monetary(string="Project Cost")
    
    last_update_color = fields.Integer(compute=_content_compute_total)
    count_members = fields.Float(string='Members', compute=_content_compute_total, digits=(12,3))
    total_salary = fields.Monetary(string="Salary Cost", compute=_content_compute_total)
    profit = fields.Monetary(string="Profit", compute=_content_compute_total)
    
    member_ids = fields.One2many('project.member.management', 'project_management_id', string="Members")
    project_expense_management = fields.One2many('project.expense.management', 'project_management_id', string="Project Cost Management")
    project_management_history = fields.One2many('project.management.history', 'project_management_id', string="Project Management History")
    
    
    project_type_id = fields.Many2one("project.type", string="Project Type")
    
    user_login = fields.Many2one('res.users', string="User")
    sub_user_login = fields.Many2one('res.users', string="Sub CEO")
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH project_estimation_merged AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY pr.id ASC) AS id,
                        pr.id AS project_id,
                        pr.user_id AS user_pm,
                        pr.department_id,
                        pr.company_id,
                        pr.date_start,
                        pr.date AS date_end,
                        pr.last_update_status AS status,
                        est.project_type_id,
                        est.currency_id,

                        (SELECT 
                            SUM(pe.total_expenses) 
                        FROM project_expense_management AS pe 
                        WHERE pe.project_id = pr.id
                        ) AS project_cost,

                        (CASE 
                            WHEN est.stage = (SELECT id 
                                                FROM estimation_status 
                                            WHERE type = 'completed')
                                THEN est.total_cost
                            ELSE 0
                        END
                        ) AS total_cost

                    FROM
                        project_project AS pr 
                    LEFT JOIN estimation_work AS est
                        ON est.id = pr.estimation_id
                    WHERE (EXTRACT(MONTH FROM pr.date_start) < EXTRACT(MONTH FROM CURRENT_DATE)
                        AND EXTRACT(YEAR FROM pr.date_start) = EXTRACT(YEAR FROM CURRENT_DATE))
                        OR EXTRACT(YEAR FROM pr.date_start) < EXTRACT(YEAR FROM CURRENT_DATE)

                    GROUP BY
                        project_id,
                        est.project_type_id,
                        user_pm,
                        pr.department_id,
                        pr.company_id,
                        pr.date_start,
                        date_end,
                        status,
                        est.stage,
                        est.total_cost,
                        est.currency_id,
                        project_cost
                    ),
                    project_management_compute AS (
                        SELECT
                            pem.id,
                            pem.project_id,
                            pem.project_type_id,
                            pem.user_pm,
                            pem.department_id,
                            pem.company_id,
                            pem.date_start,
                            pem.date_end,
                            pem.status,
                            --- Handling when value is null ---
                            (SELECT COALESCE(NULLIF(pem.project_cost, NULL), 0)) AS project_cost,

                            (CASE 
                            --- Get total cost when estimation exists ---
                                WHEN pem.total_cost <> 0 
                                    THEN (CASE 
                                            WHEN pem.currency_id = (SELECT id FROM estimation_currency WHERE name = 'USD')
                                                THEN pem.total_cost * (SELECT usd_convert FROM api_exchange_rate)
                                            WHEN pem.currency_id = (SELECT id FROM estimation_currency WHERE name = 'JPY')
                                                THEN pem.total_cost * (SELECT jpy_convert FROM api_exchange_rate)
                                            ELSE pem.total_cost
                                        END
                                    )
                            --- Get project revenue VND when estimation does not exists ---
                                WHEN prm.revenue_vnd IS NOT NULL AND prm.revenue_vnd <> 0
                                    THEN prm.revenue_vnd
                                ELSE 0
                            END
                            ) AS revenue

                        FROM project_estimation_merged AS pem
                        LEFT JOIN project_revenue_management AS prm
                            ON pem.project_id = prm.project_id
                    )
                    SELECT
                        pmc.id,
                        pmc.project_id,
                        pmc.project_type_id,
                        pmc.user_pm,
                        pmc.department_id,
                        pmc.company_id,
                        pmc.date_start,
                        pmc.date_end,
                        pmc.status,
                        pmc.project_cost,
                        pmc.revenue,
                        he.user_id AS user_login,
                        ru.id AS sub_user_login,
		                cr.id AS currency_id
                    FROM project_management_compute AS pmc
                    LEFT JOIN hr_department AS hd
                        ON hd.id = pmc.department_id
                    LEFT JOIN hr_employee AS he
                        ON he.id = hd.manager_id
                    LEFT JOIN res_company AS rc
                        ON rc.id = pmc.company_id
                    LEFT JOIN res_users AS ru
                        ON ru.login = rc.user_email
                    LEFT JOIN res_currency AS cr
		                ON cr.name = 'VND'

            ) """ % (self._table)
        )