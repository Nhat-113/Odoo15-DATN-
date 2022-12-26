from odoo import fields, models, tools


class ProjectManagement(models.Model):
    _name = "project.management"
    _description = "Project Management"
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH project_estimation_merged AS (
                    SELECT
                        -- ROW_NUMBER() OVER(ORDER BY pr.id ASC) AS id,
                        pr.id AS project_id,
                        pr.user_id AS user_pm,
                        pr.department_id,
                        pr.company_id,
                        pr.date_start,
                        pr.date AS date_end,
                        pr.last_update_status AS status,
                        pr.stage_id,
                        pps.name AS stage_name,
                        pr.project_type AS project_type_id,
                        est.currency_id,
                        ec.name AS est_currency_name,
                        pem.expense_vnd AS project_cost,

                        (CASE 
                            WHEN es.type = 'completed'
                                THEN est.total_cost
                            ELSE 0
                        END
                        ) AS total_cost

                    FROM project_project AS pr 
                    LEFT JOIN estimation_work AS est
                        ON est.id = pr.estimation_id
                    LEFT JOIN project_expense_management AS pem
                        ON pem.project_id = pr.id
                    LEFT JOIN estimation_currency AS ec
                        ON ec.id = est.currency_id
                    LEFT JOIN estimation_status AS es
                        ON es.id = est.stage
                    LEFT JOIN project_project_stage AS pps
		                ON pps.id = pr.stage_id
                    WHERE EXTRACT(YEAR FROM pr.date_start) = EXTRACT(YEAR FROM CURRENT_DATE) OR
                        EXTRACT(YEAR FROM pr.date) = EXTRACT(YEAR FROM CURRENT_DATE) OR
                        (EXTRACT(YEAR FROM CURRENT_DATE) >= EXTRACT(YEAR FROM pr.date_start) AND
                            EXTRACT(YEAR FROM CURRENT_DATE) <= EXTRACT(YEAR FROM pr.date))

                    GROUP BY
                        pr.id,
                        est.project_type_id,
                        user_pm,
                        pr.department_id,
                        pr.company_id,
                        pr.date_start,
                        date_end,
                        status,
                        stage_id,
                        stage_name,
                        est.stage,
                        est.total_cost,
                        est.currency_id,
                        est_currency_name,
                        project_cost,
                        es.type
                    ),
                    project_management_compute AS (
                        SELECT
                            -- pem.id,
                            pem.project_id,
                            pem.project_type_id,
                            pem.user_pm,
                            pem.department_id,
                            pem.company_id,
                            pem.date_start,
                            pem.date_end,
                            pem.status,
                            pem.stage_id,
                            pem.stage_name,
                            --- Handling when value is null ---
                            (SELECT COALESCE(NULLIF(pem.project_cost, NULL), 0)) AS project_cost,

                            (CASE 
                                --- Get project revenue VND exists ---
                                WHEN prm.revenue_vnd IS NOT NULL AND prm.revenue_vnd <> 0
                                    THEN prm.revenue_vnd
                            
                            --- Get total cost when project revenue does not exists ---
                                WHEN pem.total_cost <> 0 
                                    THEN (CASE 
                                            WHEN pem.est_currency_name = 'USD'
                                                THEN pem.total_cost * (SELECT usd_convert FROM api_exchange_rate)
                                            WHEN pem.est_currency_name = 'JPY'
                                                THEN pem.total_cost * (SELECT jpy_convert FROM api_exchange_rate)
                                            WHEN pem.est_currency_name = 'SGD'
                                                THEN pem.total_cost * (SELECT sgd_convert FROM api_exchange_rate)
                                            ELSE pem.total_cost
                                        END
                                    )
                            
                                ELSE 0
                            END
                            ) AS revenue,
                            (CASE
                                WHEN prm.revenue_vnd IS NOT NULL AND prm.revenue_vnd <> 0
                                    THEN 'project_revenue'
                                WHEN pem.total_cost <> 0 
                                    THEN 'estimation'
                                ELSE 'null'
                            END) AS revenue_from,
                            prm.total_commission::NUMERIC(20, 4)

                        FROM project_estimation_merged AS pem
                        LEFT JOIN project_revenue_management AS prm
                            ON pem.project_id = prm.project_id
                        WHERE pem.department_id NOT IN (SELECT department_id FROM department_mirai_fnb) 
                            OR pem.department_id IS NULL
                    )
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY project_id ASC) AS id,
                        pmc.project_id,
                        pmc.project_type_id,
                        pmc.user_pm,
                        pmc.department_id,
                        pmc.company_id,
                        pmc.date_start,
                        pmc.date_end,
                        pmc.status,
                        pmc.stage_id,
                        pmc.stage_name,
                        pmc.project_cost,
                        pmc.revenue,
                        pmc.total_commission,
                        pmc.revenue_from,
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
       

class ProjectManagementData(models.Model):
    _name = "project.management.data"
    _description = "Project Management"
    _rec_name = "project_id"
    

    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one("hr.department", string="Department")
    user_pm = fields.Many2one('res.users', string="PM")
    company_id = fields.Many2one('res.company', string="Company")
    currency_id = fields.Many2one('res.currency', string="Currency")
    date_start = fields.Date(string='Start')
    date_end = fields.Date(string='End')
    status = fields.Selection(related='project_id.last_update_status', string='Status')
    stage_id = fields.Many2one('project.project.stage', string="Stage")
    stage_name = fields.Char(string='Stage Name')
    
    # bonus = fields.Float(string="Bonus")
    revenue = fields.Float(string="Revenue")
    total_commission = fields.Float(string="Commission")
    project_cost = fields.Float(string="Prj Expenses")
    total_avg_operation_project = fields.Float(string="Operation Prj")
    total_department_expense = fields.Float(string="Dpm Expenses", help="Total Department Expenses By Month")
    
    last_update_color = fields.Integer(related='project_id.last_update_color', store=False)
    count_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2), help="Profit Margin = profit / revenue * 100")
    
    member_ids = fields.One2many('project.management.member.data', 'project_management_id', string="Members")
    project_expense_values = fields.One2many('project.expense.value', 'project_management_id', string="Project Cost Management")
    project_management_history = fields.One2many('project.management.history.data', 'project_management_id', string="Project Management History")
    project_management_request_overtimes = fields.One2many('project.management.request.overtime.data', 'project_management_id', string="Overtime Detail")
    project_management_history_temp = fields.One2many('project.history.group.temp', 'project_management_id', string="Project Management History Temp")
    
    
    project_type_id = fields.Many2one("project.type", string="Project Type")
    
    user_login = fields.Many2one('res.users', string="User")
    sub_user_login = fields.Many2one('res.users', string="Sub CEO")