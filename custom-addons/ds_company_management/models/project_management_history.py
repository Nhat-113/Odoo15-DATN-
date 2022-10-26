from odoo import fields, models, tools, api
import datetime

class ProjectManagementHistory(models.Model):
    _name = "project.management.history"
    _description = "Project Management History"
    _auto = False
    _order = "month_start desc"
    
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id)
    months = fields.Char(string="Month")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    working_day = fields.Float(string="Working day")
    total_project_expense = fields.Float(string="Project Cost", help="Total Project Expenses By Month")
    operation_cost = fields.Float(string="Operation Cost", help="Total Operation Cost")
    average_cost_company = fields.Float(string="Company Avg Cost")
    average_cost_project = fields.Float(string="Prj Avg Cost")
    members = fields.Float(string="Effort(MM)", digits=(12,3))
    all_members = fields.Float(string="Total members", digits=(12,3))
    
    total_salary = fields.Float(string="Salary Cost", help="Total salary Employees By Month = SUM(salary_employee * effort_rate)")
    revenue = fields.Float(string="Revenue", help="Revenue By Month")
    profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2), help="Profit Margin = profit / revenue * 100")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH extract_month_project AS (
                    --- Generate month from date_start & date_end project ---
                    SELECT 
                        pm.id AS project_management_id,
                        pm.project_id,
                        pm.company_id,
                        generate_series(
                            date_trunc('month', min(pm.date_start)), 
                            date_trunc('month', max(pm.date_end)), 
                            '1 month'
                        )::date AS months,
                        pm.date_start,
                        pm.date_end,
                        pm.revenue,
                        pm.revenue_from

                    FROM project_management AS pm
                    GROUP BY
                        project_management_id,
                        pm.project_id,
                        pm.company_id,
                        pm.date_start,
                        pm.date_end,
                        pm.revenue,
                        pm.revenue_from
                ),

                -- get month start & month end from project ---
                generate_month_project AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                        phm.project_management_id,
                        phm.project_id,
                        phm.company_id,
                        phm.date_start,
                        phm.date_end,
                        phm.months AS first_date,
                        --- Total cost is taken from estimation or project revenue and converted to VND ---
                        phm.revenue AS total_cost,
                        phm.revenue_from,
                        prv.revenue_vnd,

                        --- Generate month_start & month_end from generate month
                        (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_start) 
                                    AND EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_start)
                            THEN phm.date_start::date
                            ELSE phm.months
                        END) AS month_start,

                        (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_end) 
                                    AND EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_end)
                            THEN phm.date_end::date
                            ELSE (SELECT date_trunc('month', phm.months) + interval '1 month - 1 day')::date
                        END) AS month_end

                    FROM extract_month_project AS phm 
                    LEFT JOIN project_revenue_value AS prv
                        ON prv.project_id = phm.project_id
                        AND prv.get_month::int = EXTRACT(MONTH FROM phm.months)
                        AND prv.get_year::int = EXTRACT(YEAR FROM phm.months)
                    ORDER By project_id
                ),

                project_count_member AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                        ppb.company_id,
                        ppb.project_id,
                        ppb.months,
                        (SUM(ppb.man_month)) AS total_members
                    FROM project_planning_booking AS ppb
                    GROUP BY company_id,
                            project_id,
                            months
                ),

                project_count_member_not_intern AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                        ppb.company_id,
                        ppb.project_id,
                        ppb.months,
                        (SUM(ppb.man_month)) AS total_members
                    FROM project_planning_booking AS ppb
                    WHERE ppb.member_type_name NOT IN ('Intern', 'intern') 
                            OR ppb.member_type_name IS NULL
                    GROUP BY company_id,
                            project_id,
                            months
                ),

                company_count_member_not_intern AS (
                    -- count total employee (unique) from booking resource by month
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                        company_id,
                        months,
                        COUNT(DISTINCT (employee_id)) all_members
                    FROM project_planning_booking AS ppb
                    WHERE ppb.member_type_name NOT IN ('Intern', 'intern') 
                            OR ppb.member_type_name IS NULL
                    GROUP BY company_id, months
                ),

                --- project expense management generate month ---

                project_expense_value_month AS (
                    SELECT 
                        pev.project_id,
                        pev.expense_date,
                        date_trunc('month', pev.expense_date)::DATE AS months,
                        pev.expense_vnd
                        
                    FROM project_expense_value AS pev
                ),

                -- compute total project expense management by month ---
                project_expense_value_total AS (
                    SELECT
                        project_id,
                        months,
                        (Sum(expense_vnd)) AS total_project_expense

                    FROM project_expense_value_month
                    GROUP BY project_id,
                            months
                ),

                compute_total_salary_employee AS (
                    SELECT
                        company_id,
                        project_id,
                        months,
                        sum(salary)::NUMERIC(20, 5) AS salary
                        
                    FROM project_planning_booking 
                    WHERE member_type_name NOT IN('Intern', 'intern')
                        OR member_type_name IS NULL
                    GROUP BY company_id,
                            project_id,
                            months

                ),

                --- Compute total cost, working day, member by month ---
                project_compute_value_by_month AS (
                    SELECT 
                        gmp.project_management_id,
                        gmp.company_id,
                        gmp.project_id,
                    --  gmp.date_start,
                    --  gmp.date_end,
                        gmp.month_start,
                        gmp.month_end,
                        
                        --- Compute working day by month of project ---
                        (SELECT COUNT(*)
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(
                                    gmp.month_start, 
                                    gmp.month_end, 
                                    interval '1 day'
                                ) AS dd 
                            ) AS days
                            WHERE dw NOT IN (6,0)
                        ) AS working_day,
                        
                        (SELECT COUNT(*)
                            FROM (
                                SELECT dd, 
                                        EXTRACT(DOW FROM dd) AS dw
                                FROM generate_series(
                                        gmp.first_date, 
                                        (date_trunc('month', gmp.first_date) + interval '1 month - 1 day')::DATE, 
                                        interval '1 day'
                                    ) AS dd 
                                ) AS days
                            WHERE dw NOT IN (6,0)
                        ) AS total_working_day,
                        
                        gmp.total_cost,
                        gmp.revenue_from,
                        gmp.revenue_vnd,
                        (COALESCE(NULLIF(cts.salary, NULL), 0)) AS total_salary,
                        (COALESCE(NULLIF(pevt.total_project_expense, NULL), 0)) AS total_project_expense,
                        (COALESCE(NULLIF(em.total_expenses, NULL), 0)) AS operation_cost,
                        (COALESCE(NULLIF(pcm.total_members, NULL), 0))::NUMERIC(20, 4) AS members_project,
                        (COALESCE(NULLIF(pni.total_members, NULL), 0))::NUMERIC(20, 4) AS members_project_not_intern,
                        (COALESCE(NULLIF(cni.all_members, NULL), 0)) AS all_members,
                        
                        (CASE 
                            WHEN cni.all_members = 0 OR cni.all_members IS NULL
                                THEN 0
                            ELSE (COALESCE(NULLIF(em.total_expenses, NULL), 0)) / cni.all_members::numeric(10, 4)
                        END)::numeric(20, 4) AS average_cost_company
                        
                        
                    FROM generate_month_project AS gmp
                    LEFT JOIN project_expense_value_total AS pevt
                        ON pevt.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pevt.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pevt.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN expense_management AS em
                        ON em.company_id = gmp.company_id
                        AND em.get_month::int = EXTRACT(MONTH FROM gmp.month_start)
                        AND em.get_year::int = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN compute_total_salary_employee AS cts
                        ON cts.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM cts.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM cts.months) = EXTRACT(YEAR FROM gmp.month_start) 
                    
                    LEFT JOIN project_count_member AS pcm
                        ON pcm.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pcm.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pcm.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN project_count_member_not_intern AS pni
                        ON pni.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pni.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pni.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN company_count_member_not_intern AS cni
                        ON cni.company_id = gmp.company_id
                        AND EXTRACT(MONTH FROM cni.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM cni.months) = EXTRACT(YEAR FROM gmp.month_start)
                ),

                --- Compute total salary employee & revenue project by month ---
                project_compute_average_cost_project AS (
                    SELECT *, 
                        
                            ((pcv.working_day::decimal / pcv.total_working_day)::numeric(6, 4)) AS duration_month,
                            
                            (CASE 
                                WHEN pcv.members_project_not_intern = 0 OR pcv.total_project_expense = 0
                                    THEN pcv.average_cost_company
                                ELSE (pcv.average_cost_company + (pcv.total_project_expense::decimal / pcv.members_project_not_intern))
                            END)::numeric(20, 4) AS average_cost_project

                    FROM project_compute_value_by_month AS pcv
                    
                ),

                project_total_duration_month AS (
                    SELECT
                        project_id,
                        (SUM(duration_month)) AS total_duration_month
                        
                    FROM project_compute_average_cost_project
                    GROUP BY project_id

                ),
                compute_project_revenue AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                        pac.project_management_id,
                        pac.company_id,
                        pac.project_id,
                        pac.month_start,
                        pac.month_end,
                        pac.working_day,
                        pac.total_cost,
                        pac.total_salary,
                        pac.total_project_expense,
                        pac.operation_cost,
                        pac.members_project AS members,
                        pac.members_project_not_intern,
                        pac.all_members,
                        pac.average_cost_company,
                        pac.average_cost_project,
                        pac.duration_month,
                        (CASE
                            WHEN pac.revenue_from = 'project_revenue'
                                THEN COALESCE(NULLIF(pac.revenue_vnd, NULL), 0)
                            WHEN pac.revenue_from = 'estimation'
                                THEN pac.duration_month * pac.total_cost / pdm.total_duration_month
                            ELSE
                                pac.total_cost
                        END) AS revenue,
                        rc.id AS currency_id
                    FROM project_compute_average_cost_project AS pac
                    LEFT JOIN project_total_duration_month AS pdm
                        ON pdm.project_id = pac.project_id
                    LEFT JOIN res_currency AS rc
                        ON rc.name = 'VND'
                )

                SELECT 
                        *,
                        (CONCAT((EXTRACT(YEAR FROM cpr.month_start))::text, ' ', TO_CHAR(cpr.month_start, 'Month'))) AS months,
                        (cpr.revenue - (cpr.members_project_not_intern 
                                        * cpr.average_cost_project 
                                        + cpr.total_salary)
                        ) AS profit,
                        (CASE
                            WHEN cpr.revenue = 0
                                THEN 0
                            ELSE (cpr.revenue - (cpr.members_project_not_intern 
                                                * cpr.average_cost_project 
                                                + cpr.total_salary)
                                    ) / cpr.revenue * 100
                        END) AS profit_margin
                FROM compute_project_revenue AS cpr
                ORDER BY company_id, project_id,  month_start

            )""" % (self._table)
        )
    

            