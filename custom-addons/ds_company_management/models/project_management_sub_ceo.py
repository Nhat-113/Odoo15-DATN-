from odoo import fields, models, tools


class ProjectManagementSubCeo(models.Model):
    _name = 'project.management.subceo'
    _description = 'Project Management Sub CEO'
    _auto = False
    _order = "id desc"
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH project_history_department AS (
                    SELECT
                        pm.company_id,
                        pm.department_id,
                        -- get first day of month ---
                        (date_trunc('month', pmh.month_start))::date AS month_start,
                        pmh.members,
                        pmh.total_project_expense AS project_cost,
                        pmh.profit,
                        pmh.total_salary AS salary_cost,
                        pmh.revenue,
                        pmh.total_commission,
                        pmh.average_cost_company,
                        pmh.currency_id

                    FROM project_management AS pm
                    RIGHT JOIN project_management_history AS pmh
                            ON pm.id = pmh.project_management_id
                ),

                --- Group by company, department, month of project history management ---
                project_history_department_group AS (
                        SELECT
                                phd.company_id,
                                phd.department_id,
                                phd.month_start,
                                (SUM (phd.members)) AS members,
                                (SUM (phd.project_cost)) AS project_cost,
                                (SUM (phd.revenue)) AS revenue,
                                (SUM (phd.total_commission)) AS total_commission,
                                (SUM (phd.salary_cost)) AS salary_cost,
                                (SUM (phd.profit)) AS profit,
                                phd.average_cost_company,
                                phd.currency_id
                                
                        FROM project_history_department AS phd
                        GROUP BY
                                phd.company_id,
                                phd.department_id,
                                phd.month_start,
                                phd.average_cost_company,
                                phd.currency_id
                ),

                --- compute max duration for generate month for department by revenue management of company expense
                compute_max_duration_department AS (
                    SELECT
                        (CASE
                            WHEN max(sort_date) < CURRENT_DATE::DATE
                                THEN (date_trunc('month',CURRENT_DATE))::DATE
                            ELSE max(sort_date)
                        END) AS max_months,
                        pp.department_id
                    FROM project_revenue_value AS prv
                    LEFT JOIN project_project AS pp
                        ON pp.id = prv.project_id
                    GROUP BY pp.department_id
                ),

                department_by_month AS (
                    SELECT
                        generate_series(
                                date_trunc('month', '1/1/2021'::date), 
                                date_trunc('month', 
                                    (CASE
										WHEN cm.max_months IS NULL
											THEN (date_trunc('month',CURRENT_DATE))::DATE
										ELSE cm.max_months
									END)
                                ),
                                '1 month'
                        )::date AS months,
                        hd.id AS department_id,
                        hd.manager_id,
                        hd.company_id
                        
                        FROM hr_department AS hd
                        LEFT JOIN compute_max_duration_department AS cm
                            ON cm.department_id = hd.id
                        WHERE hd.id NOT IN (SELECT department_id FROM department_mirai_fnb)
                ),

                compute_salary_manager_department AS (
                    SELECT
                        dbm.company_id,
                        dbm.department_id,
                        mdh.manager_id,
                        mdh.manager_history_id,
                        mdh.month_start,
                        mdh.month_end,
                        mdh.working_day,
                        mdh.working_day_total,
                        mdh.bqnc,
                        mdh.bhxh,
                        mdh.ttncn,
                        mdh.salary_manager,
                        mdh.effort_rate_month,
                        mdh.man_month,
                        dbm.months,
                        (CASE
                            --- When have change manager department ----
                            WHEN mdh.manager_history_id IS NOT NULL
                                THEN (CASE
                                        --- when doesn't payslip of the manager department---
                                        WHEN mdh.salary_manager IS NULL
                                            THEN 0
                                        ELSE
                                            (CASE
                                                --- when the manager quits in the middle of the month ---
                                                WHEN mdh.working_day <> mdh.working_day_total
                                                    THEN (CASE
                                                            --- when manager doesn't booked ---
                                                            WHEN mdh.effort_rate_month IS NULL
                                                                THEN (mdh.bqnc + (mdh.bhxh + mdh.ttncn) / mdh.working_day_total) * mdh.working_day
                                                            ELSE
                                                                (mdh.bqnc + (mdh.bhxh + mdh.ttncn) / mdh.working_day_total) * mdh.working_day * (100 - mdh.effort_rate_month) / 100
                                                        END)
                                                ELSE 
                                                    (CASE
                                                        WHEN mdh.effort_rate_month IS NULL
                                                            THEN mdh.salary_manager + mdh.bhxh + mdh.ttncn
                                                        ELSE
                                                            (mdh.salary_manager + mdh.bhxh + mdh.ttncn) *((100 - mdh.effort_rate_month )/ 100)
                                                    END)
                                            END)
                                    END)
                            --- when manager doesn't change ---
                            ELSE
                                (CASE
                                    --- when doesn't payslip of the manager department---
                                    WHEN mdh.salary_manager IS NULL
                                        THEN 0
                                    ELSE
                                        (CASE
                                            --- when manager doesn't booked ---
                                            WHEN mdh.effort_rate_month IS NULL
                                                THEN mdh.salary_manager + mdh.bhxh + mdh.ttncn
                                            ELSE
                                                (mdh.salary_manager + mdh.bhxh + mdh.ttncn) * ((100 - mdh.effort_rate_month) / 100)
                                        END)
                                
                                END)
                        END)::NUMERIC(20,4) AS remaining_salary,
                        
                        (CASE
                            WHEN mdh.effort_rate_month IS NULL
                                THEN (mdh.working_day::NUMERIC(10,5) / mdh.working_day_total)::NUMERIC(10,5)
                            ELSE
                                (CASE
                                    WHEN mdh.effort_rate_month = 100
                                        THEN 0
                                    ELSE
                                        ((mdh.working_day::NUMERIC(10,5) / mdh.working_day_total) * ((100.00 - mdh.effort_rate_month)/ 100))::NUMERIC(10,5)
                                END)
                        END) AS remaining_member
                        
                    FROM department_by_month AS dbm
                    LEFT JOIN manager_department_history AS mdh
                        ON mdh.company_id = dbm.company_id
                        AND mdh.department_id = dbm.department_id
                        AND EXTRACT(MONTH FROM mdh.month_start) = EXTRACT(MONTH FROM dbm.months)
                        AND EXTRACT(YEAR FROM mdh.month_start) = EXTRACT(YEAR FROM dbm.months)
                ),

                compute_salary_manager_department_group AS (
                    SELECT
                        cs.company_id,
                        cs.department_id,
                        cs.manager_id,
                        cs.months,
                        (SUM( cs.remaining_salary )) AS remaining_salary_manager,
                        (SUM( cs.remaining_member )) AS remaining_member

                    FROM compute_salary_manager_department AS cs
                    GROUP BY
                        cs.months,
                        cs.company_id,
                        cs.department_id,
                        cs.manager_id
                )
                    
                SELECT
                    ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                    csg.company_id,
                    csg.department_id,
                -- 	csg.manager_id,
                    (CONCAT((EXTRACT(YEAR FROM csg.months))::text, ' ', TO_CHAR(csg.months, 'Month'))) AS months,
                    csg.months AS month_start,
                    (date_trunc('month', csg.months) + interval '1 month - 1 day'
                        )::date AS month_end,
                -- 	csg.remaining_salary_manager,
                -- 	csg.remaining_member,
                -- 	phdg.average_cost_company,

                    -- remaining_member & remaining_salary manager have been calculated
                    COALESCE(NULLIF(phdg.members,		NULL), 0) + csg.remaining_member  AS total_members,
                    COALESCE(NULLIF(phdg.project_cost,	NULL), 0)  AS total_project_cost,
                    COALESCE(NULLIF(phdg.revenue, 		NULL), 0)  AS total_revenue,
                    COALESCE(NULLIF(phdg.total_commission, NULL), 0)  AS total_commission,
                    COALESCE(NULLIF(phdg.salary_cost, 	NULL), 0) + csg.remaining_salary_manager AS total_salary,
                    COALESCE(NULLIF(phdg.profit, 		NULL), 0) - csg.remaining_salary_manager AS total_profit,
                    COALESCE(
                        NULLIF(phdg.currency_id, NULL), 
                                (SELECT id FROM res_currency 
                                    WHERE name = 'VND')
                    )  AS currency_id,
                    ru.id AS user_login
                    
                FROM compute_salary_manager_department_group AS csg
                LEFT JOIN project_history_department_group AS phdg
                    ON phdg.company_id = csg.company_id
                    AND phdg.department_id = csg.department_id
                    AND phdg.month_start = csg.months
                LEFT JOIN res_company AS rc
                    ON rc.id = csg.company_id
                LEFT JOIN res_users AS ru
                    ON ru.login = rc.user_email
                ORDER BY company_id, department_id, months

            ) """ % (self._table)
        )
        
        
    
   
    

class ProjectManagementSubCeoData(models.Model):
    _name = 'project.management.subceo.data'
    _description = 'Project Management Sub CEO Data'
    _order = "id desc"
     
    
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    months = fields.Char(string="Month")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    total_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_project_cost = fields.Float(string="Prj Expenses")
    total_revenue = fields.Float(string="Revenue")
    total_commission = fields.Float(string="Commission")
    total_profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2))
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    user_login = fields.Many2one('res.users', string="User")
    
         
    def get_project_detail(self):
        action = {
            'name': self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'department.project.detail.data',
            'view_ids': self.env.ref('ds_company_management.department_project_detail_action').id,
            'view_mode': 'tree',
            'domain': [('department_id', '=', self.department_id.id), 
                       ('company_id', '=', self.company_id.id),
                       ('months_domain', 'in', [self.month_start, self.month_end])]
        }
        return action