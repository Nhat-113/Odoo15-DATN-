from odoo import fields, models, tools, api
import datetime

class ProjectManagementHistory(models.Model):
    _name = "project.management.history"
    _description = "Project Management History"
    _auto = False
    _order = "month_start desc"
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH check_project_status AS (
                    SELECT 
                        project_id,
                        date
                        --status
                    FROM project_update
                    WHERE status = 'off_track'
                ),

                compute_duration_project AS (
                    SELECT 
                        pm.id AS project_management_id,
                        pm.project_id,
                        pm.company_id,
                        pm.department_id,
                        pm.stage_name,
                        pm.date_start,
                        (CASE
                            WHEN cp.date IS NULL
                                THEN pm.date_end
                            ELSE cp.date
                        END)::date AS date_end,
                        pm.revenue,
                        pm.revenue_from

                    FROM project_management AS pm
                    LEFT JOIN check_project_status AS cp
                        ON cp.project_id = pm.project_id
                ),

                extract_month_project AS (
                    --- Generate month from date_start & date_end project ---
                    SELECT 
                        pm.project_management_id,
                        pm.project_id,
                        pm.company_id,
                        pm.department_id,
                        pm.stage_name,
                        generate_series(
                            date_trunc('month', min(pm.date_start)), 
                            date_trunc('month', max(pm.date_end)), 
                            '1 month'
                        )::date AS months,
                        pm.date_start,
                        pm.date_end,
                        pm.revenue,
                        pm.revenue_from

                    FROM compute_duration_project AS pm
                    GROUP BY
                        project_management_id,
                        pm.project_id,
                        pm.company_id,
                        pm.department_id,
                        pm.stage_name,
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
                        phm.department_id,
                        phm.stage_name,
                        phm.date_start,
                        phm.date_end,
                        phm.months AS first_date,
                        --- Total cost is taken from estimation or project revenue and converted to VND ---
                        phm.revenue AS total_cost,
                        phm.revenue_from,
                        prv.revenue_vnd,
                        (COALESCE(NULLIF(prv.result_commission, NULL), 0))::NUMERIC(20, 4) AS result_commission,

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

                compute_project_count_member AS (
                    --SELECT
                        --company_id,
                        --project_id,
                        --months,
                        --SUM(man_month) AS total_members,
                        --SUM(salary)::NUMERIC(20, 5) AS salary
                    --FROM project_planning_booking
                        --WHERE department_id NOT IN (SELECT department_id FROM department_mirai_fnb) 
                            --OR department_id IS NULL
                    --GROUP BY company_id,
                            --project_id,
                            --months
                    SELECT
                        project_id,
                        months,
                        SUM(mm)::NUMERIC(10, 2) AS total_members
                        --SUM(salary) AS salary
                    FROM project_count_member_contract
                    WHERE department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                        OR department_id IS NULL
                    GROUP BY project_id, months
                ),
                
                compute_project_total_salary AS (
                    SELECT
                        project_id,
                        months,
                        SUM(salary) AS salary
                    FROM project_planning_booking
                    GROUP BY project_id,
                        months
                ),

                project_count_member_not_intern AS (
                    -- 	SELECT
                    -- 		company_id,
                    -- 		project_id,
                    -- 		months,
                    -- 		SUM(man_month) AS total_members
                    -- 	FROM project_planning_booking
                    -- 	WHERE (member_type_name NOT IN ('Intern', 'intern') 
                    -- 			OR member_type_name IS NULL)
                    -- 			AND (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                    -- 					OR department_id IS NULL)
                    -- 	GROUP BY company_id,
                    -- 			project_id,
                    -- 			months
                        SELECT
                            project_id,
                            months,
                            SUM(mm)::NUMERIC(10, 2) AS total_members
                        FROM project_count_member_contract
                        WHERE (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                            OR department_id IS NULL) AND type_contract = 'official'
                        GROUP BY project_id, months
                ),
                pesudo_contract_count_member AS (
                    SELECT
                        company_id,
                        employee_id,
                        months,
                        --working_day,
                        --total_working_day,
                        SUM(working_day::DECIMAL / total_working_day::DECIMAL)::NUMERIC(10, 2) AS mm
                    FROM pesudo_contract
                    WHERE contract_document_type != 'internship' 
                    GROUP BY company_id,
                            employee_id,
                            months
                ),

                company_count_member_not_intern AS (
                    SELECT
                        company_id,
                        months,
                        SUM(mm) AS all_members
                    FROM pesudo_contract_count_member
                    GROUP BY company_id, months
                ),

                -- company_count_member_not_intern AS (
                -- 	-- count total employee (unique) from booking resource by month
                -- 	SELECT
                -- 		ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                -- 		company_id,
                -- 		months,
                -- 		COUNT(DISTINCT (employee_id)) all_members
                -- 	FROM project_planning_booking AS ppb
                -- 	WHERE (ppb.member_type_name NOT IN ('Intern', 'intern') 
                -- 			OR ppb.member_type_name IS NULL)
                -- 			AND (ppb.department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                -- 				OR ppb.department_id IS NULL)
                -- 	GROUP BY company_id, months
                -- ),

                --- project expense management generate month ---

                project_expense_value_month AS (
                    SELECT 
                        project_expense_management_id,
                        department_id,
                        project_id,
                        expense_date,
                        date_trunc('month', expense_date)::DATE AS months,
                        expense_vnd
                        
                    FROM project_expense_value
                ),

                -- compute total project expense management by month ---
                project_expense_value_total AS (
                    SELECT
                        project_id,
                        months,
                        (Sum(expense_vnd)) AS total_project_expense

                    FROM project_expense_value_month
                    WHERE project_id IS NOT NULL
                        AND project_expense_management_id IS NOT NULL
                    GROUP BY project_id,
                            months
                ),

                department_expense_value_total AS (
                    SELECT
                        department_id,
                        expense_date,
                        sum(expense_vnd) AS total_project_expense

                    FROM project_expense_value
                    WHERE project_id IS NULL
                    GROUP BY department_id,
                            expense_date
                ),

                project_management_department_merged AS (
                    SELECT
                        pm.department_id,
                        gmp.project_id,
                        gmp.month_start,
                        gmp.month_end
                    FROM project_management AS pm
                    RIGHT JOIN generate_month_project AS gmp
                        ON gmp.project_management_id = pm.id
                ),

                compare_project_department_expense AS (
                    SELECT
                        dev.department_id,
                        dev.expense_date,
                        dev.total_project_expense,
                        pmd.project_id
                        
                    FROM department_expense_value_total AS dev
                    LEFT JOIN project_management_department_merged AS pmd
                        ON dev.department_id = pmd.department_id
                        AND dev.expense_date BETWEEN pmd.month_start AND pmd.month_end
                ),

                compute_count_department_expense_value AS (
                    SELECT 
                        department_id,
                        expense_date,
                        total_project_expense,
                        COUNT(project_id) AS counts

                    FROM compare_project_department_expense
                    GROUP BY department_id,
                            expense_date,
                            total_project_expense
                ),

                compute_project_department_expense AS (
                    SELECT
                        cpd.department_id,
                        cpd.expense_date,
                        date_trunc('month', cpd.expense_date)::DATE AS months,
                        ccd.counts,
                        cpd.project_id,
                        (CASE
                            WHEN ccd.counts = 0
                                THEN cpd.total_project_expense
                            ELSE cpd.total_project_expense / ccd.counts
                        END) AS total_project_expense
                    
                    FROM compute_count_department_expense_value AS ccd
                    RIGHT JOIN compare_project_department_expense AS cpd
                        ON cpd.department_id = ccd.department_id
                        AND cpd.expense_date = ccd.expense_date
                ),

                compute_department_project_expense_group AS (
                    SELECT
                        project_id,
                        months,
                        SUM(total_project_expense) AS total_project_expense
                    
                    FROM compute_project_department_expense
                    WHERE project_id IS NOT NULL
                    GROUP BY project_id, months
                ),


                --- Compute total salary employee & revenue project by month ---
                -- compute_total_salary_employee AS (
                -- 	SELECT
                -- 		company_id,
                -- 		project_id,
                -- 		months,
                -- 		sum(salary)::NUMERIC(20, 5) AS salary
                -- 		
                -- 	FROM project_planning_booking 
                -- 	WHERE (member_type_name NOT IN('Intern', 'intern')
                -- 			OR member_type_name IS NULL)
                -- 		AND (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                -- 			OR department_id IS NULL)
                -- 	GROUP BY company_id,
                -- 			project_id,
                -- 			months
                -- ),

                expense_management_join_company AS (
                    SELECT
                        em.id,
                        em.get_month,
                        em.get_year,
                        em.total_expenses,
                        rel.res_company_id
                    FROM expense_management AS em
                    LEFT JOIN general_expenses_company_rel AS rel
                        ON rel.expense_management_id = em.id
                ),
                    
                expense_management_count_company AS (
                    SELECT
                        expense_management_id,
                        COUNT(res_company_id) AS counts

                    FROM general_expenses_company_rel
                    GROUP BY expense_management_id
                ),

                expense_management_multiple_company AS (
                    SELECT
                        emj.get_month,
                        emj.get_year,
                        emj.total_expenses,
                        emj.res_company_id,
                        emc.counts
                    FROM expense_management_join_company AS emj
                    LEFT JOIN expense_management_count_company AS emc
                        ON emc.expense_management_id = emj.id
                ),

                compute_total_members_company AS (
                    SELECT 
                        cc.months,
                        SUM(cc.all_members) AS all_members,
                        em.id AS expense_management_id
                    -- 	cc.company_id,
                    -- 	gc.res_company_id
                        
                    FROM company_count_member_not_intern AS cc
                    LEFT JOIN expense_management_join_company AS em
                        ON em.res_company_id = cc.company_id
                        AND em.get_month::INT = EXTRACT(MONTH FROM cc.months)
                        AND em.get_year::INT = EXTRACT(YEAR FROM cc.months)
                    GROUP BY em.id, months
                ),

                compute_total_member_multi_company AS (
                    SELECT
                        ct.months,
                        ct.all_members,
                        gec.res_company_id
                    -- 	ct.expense_management_id

                    FROM compute_total_members_company AS ct
                    INNER JOIN general_expenses_company_rel AS gec
                        ON gec.expense_management_id = ct.expense_management_id
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
                        gmp.result_commission,
                        gmp.revenue_vnd,
                        (COALESCE(NULLIF(cpt.salary, NULL), 0)) AS total_salary,
                        (COALESCE(NULLIF(pevt.total_project_expense, NULL), 0)) AS total_project_expense,
                        (COALESCE(NULLIF(cdp.total_project_expense, NULL), 0)) AS total_department_expense,
                        (COALESCE(NULLIF(em.total_expenses, NULL), 0)) AS operation_cost,
                        (COALESCE(NULLIF(pcm.total_members, NULL), 0))::NUMERIC(20, 4) AS members_project,
                        (COALESCE(NULLIF(pni.total_members, NULL), 0))::NUMERIC(20, 4) AS members_project_not_intern,
                    -- 	(COALESCE(NULLIF(cni.all_members, NULL), 0)) AS all_members,
                        (CASE
                            WHEN em.counts > 1
                                THEN COALESCE(NULLIF(ctm.all_members, NULL), 0)
                            ELSE COALESCE(NULLIF(cni.all_members, NULL), 0)
                        END) AS all_members,
                        
                        (CASE 
                            WHEN cni.all_members = 0 OR cni.all_members IS NULL
                                THEN 0
                            ELSE (CASE
                                    WHEN em.counts > 1
                                        THEN COALESCE(NULLIF(em.total_expenses, NULL), 0) / ctm.all_members::NUMERIC(10, 4)
                                    ELSE
                                        COALESCE(NULLIF(em.total_expenses, NULL), 0) / cni.all_members::NUMERIC(10, 4)
                                END)
                        END)::NUMERIC(20, 4) AS average_cost_company
                        
                        
                    FROM generate_month_project AS gmp
                    LEFT JOIN project_expense_value_total AS pevt
                        ON pevt.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pevt.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pevt.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN compute_department_project_expense_group AS cdp
                        ON cdp.project_id = gmp.project_id
                        -- AND ccd.expense_date BETWEEN gmp.month_start AND gmp.month_end
                        AND EXTRACT(MONTH FROM cdp.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM cdp.months) = EXTRACT(YEAR FROM gmp.month_start)
                        -- AND gmp.stage_name != 'Done'
                        
                    LEFT JOIN expense_management_multiple_company AS em
                        ON em.res_company_id = gmp.company_id
                        AND em.get_month::int = EXTRACT(MONTH FROM gmp.month_start)
                        AND em.get_year::int = EXTRACT(YEAR FROM gmp.month_start)
                -- 		
                -- 	LEFT JOIN compute_total_salary_employee AS cts
                -- 		ON cts.project_id = gmp.project_id
                -- 		AND EXTRACT(MONTH FROM cts.months) = EXTRACT(MONTH FROM gmp.month_start)
                -- 		AND EXTRACT(YEAR FROM cts.months) = EXTRACT(YEAR FROM gmp.month_start) 
                    
                    LEFT JOIN compute_project_count_member AS pcm
                        ON pcm.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pcm.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pcm.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN compute_project_total_salary AS cpt
                        ON cpt.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM cpt.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM cpt.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN project_count_member_not_intern AS pni
                        ON pni.project_id = gmp.project_id
                        AND EXTRACT(MONTH FROM pni.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM pni.months) = EXTRACT(YEAR FROM gmp.month_start)
                        
                    LEFT JOIN company_count_member_not_intern AS cni
                        ON cni.company_id = gmp.company_id
                        AND EXTRACT(MONTH FROM cni.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM cni.months) = EXTRACT(YEAR FROM gmp.month_start)
                    LEFT JOIN compute_total_member_multi_company AS ctm
                        ON ctm.res_company_id = gmp.company_id
                        AND EXTRACT(MONTH FROM ctm.months) = EXTRACT(MONTH FROM gmp.month_start)
                        AND EXTRACT(YEAR FROM ctm.months) = EXTRACT(YEAR FROM gmp.month_start)
                ),

                project_compute_average_cost_project AS (
                    SELECT *, 
                        
                            ((pcv.working_day::decimal / pcv.total_working_day)::NUMERIC(6, 4)) AS duration_month,
                            
                            (CASE 
                                WHEN pcv.members_project = 0
                                    THEN pcv.average_cost_company
                                ELSE (pcv.average_cost_company + (
                                        (pcv.total_project_expense::decimal 
                                        + pcv.total_department_expense::decimal 
                                        + pcv.result_commission ) / pcv.members_project))
                            END)::NUMERIC(20, 4) AS average_cost_project

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
                        pac.total_department_expense,
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
                        pac.result_commission AS total_commission,
                        rc.id AS currency_id
                    FROM project_compute_average_cost_project AS pac
                    LEFT JOIN project_total_duration_month AS pdm
                        ON pdm.project_id = pac.project_id
                    LEFT JOIN res_currency AS rc
                        ON rc.name = 'VND'
                )

                SELECT 
                        *,
                        (cpr.average_cost_company * cpr.members_project_not_intern)::NUMERIC(20, 4) AS total_avg_operation_project,
                        (CONCAT((EXTRACT(YEAR FROM cpr.month_start))::text, ' ', TO_CHAR(cpr.month_start, 'Month'))) AS months,
                        (cpr.revenue - (cpr.members 
                                        * cpr.average_cost_project 
                                        + cpr.total_salary - (cpr.members - cpr.members_project_not_intern) * cpr.average_cost_company)
                        ) AS profit,
                        (CASE
                            WHEN cpr.revenue = 0
                                THEN 0
                            ELSE (cpr.revenue - (cpr.members 
                                                * cpr.average_cost_project 
                                                + cpr.total_salary- (cpr.members - cpr.members_project_not_intern) * cpr.average_cost_company)
                                    ) / cpr.revenue * 100
                        END) AS profit_margin,
                        date_trunc('month', cpr.month_start)::DATE AS months_domain
                FROM compute_project_revenue AS cpr
                ORDER BY company_id, project_id, month_start

            )""" % (self._table)
        )
    


class ProjectManagementHistoryData(models.Model):
    _name = "project.management.history.data"
    _description = "Project Management History Data"
    _order = "month_start desc"
    
    
    project_management_id = fields.Many2one('project.management.data', string="Project Management")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id)
    months = fields.Char(string="Month")
    months_domain = fields.Date(string="Month domain")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    working_day = fields.Float(string="Working day")
    total_project_expense = fields.Float(string="Prj Expenses", help="Total Project Expenses By Month")
    total_department_expense = fields.Float(string="Dpm Expenses", help="Total Department Expenses By Month")
    operation_cost = fields.Float(string="Operation Cost", help="Total Operation Cost")
    average_cost_company = fields.Float(string="Company Avg Cost")
    average_cost_project = fields.Float(string="Prj Avg Cost")
    members = fields.Float(string="Effort (MM)", digits=(12,3))
    members_project_not_intern = fields.Float(string="Effort (MM - Remove Intern)", digits=(12,3))
    all_members = fields.Float(string="Total members", digits=(12,3), help="Total members multi company not intern")
    total_avg_operation_project = fields.Float(string="Operation Prj")
    total_commission = fields.Float(string="Commission")
    
    total_salary = fields.Float(string="Salary Cost", help="Total salary Employees By Month = SUM(salary_employee * effort_rate)")
    revenue = fields.Float(string="Revenue", help="Revenue By Month")
    profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2), help="Profit Margin = profit / revenue * 100")