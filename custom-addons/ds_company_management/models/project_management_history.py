from odoo import fields, models, tools, api
import datetime

class ProjectManagementHistory(models.Model):
    _name = "project.management.history"
    _description = "Project Management History"
    _auto = False
    _order = "id desc"
    
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=lambda self: self.env.ref('base.main_company').currency_id)
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    working_day = fields.Float(string="Working day")
    total_project_expense = fields.Monetary(string="Project Cost", help="Total Project Expenses By Month")
    operation_cost = fields.Monetary(string="Operation Cost", help="Total Operation Cost")
    average_cost_company = fields.Monetary(string="Average cost company")
    average_cost_project = fields.Monetary(string="Average cost project")
    members = fields.Float(string="Members", help="Number Of Members By Month")
    all_members = fields.Float(string="Total members of company")
    
    total_salary = fields.Monetary(string="Salary Cost", help="Total salary Employees By Month = SUM(salary_employee * effort_rate)")
    revenue = fields.Monetary(string="Revenue", help="Revenue By Month")
    profit = fields.Monetary(string="Profit")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH generate_month_project AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                        phm.project_management_id,
                        phm.project_id,
                        phm.company_id,
                        phm.date_start,
                        phm.date_end,
                        --- Total cost is taken from estimation or project revenue and converted to VND ---
                        phm.revenue AS total_cost,

                        --- Generate month_start & month_end from generate month
                        (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_start) 
                                    AND EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_start)
                            THEN phm.date_start::date
                            ELSE phm.months
                        END) AS month_start,

                        (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_end) 
                                    AND	EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_end)
                            THEN phm.date_end::date
                            ELSE (SELECT date_trunc('month', phm.months) + interval '1 month - 1 day')::date
                        END) AS month_end

                    FROM (
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
                            pm.revenue

                        FROM project_management AS pm
                        GROUP BY
                            project_management_id,
                            pm.project_id,
                            pm.company_id,
                            pm.date_start,
                            pm.date_end,
                            pm.revenue
                    ) AS phm 
                    ORDER By project_id
                ),

                --- Compute total cost, working day, member by month ---
                project_compute_value_by_month AS (
                    SELECT *, (
                        --- Compute total operation cost by month ---
                        SELECT 
                            --- Handling when value is null ---
                                (SELECT COALESCE(NULLIF(SUM(eg.total_expenses), NULL), 0))
                            FROM expense_general AS eg
                            INNER JOIN expense_management AS em
                                ON eg.expense_management_id = em.id
                            WHERE em.get_month::int = EXTRACT (MONTH FROM prhm.month_start)
                                AND em.get_year::int = EXTRACT (YEAR FROM prhm.month_start)
                        ) AS operation_cost,
                        
                        --- Compute duration month equal man month follow working day ---
                        
                        ((prhm.working_day::decimal / 20)::numeric(6, 3)) AS duration_month
                        
                    FROM (
                        SELECT  *, (
                                --- Compute working day by month
                                SELECT COUNT(*)
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
                                
                                --- Compute total project cost by month---
                                (SELECT 
                                    --- Handling when value is null ---
                                        (SELECT coalesce(NULLIF(SUM(pem.expense_vnd), NULL), 0))
                                    FROM project_expense_management AS pem
                                    WHERE pem.project_id = gmp.project_id 
                                        AND pem.expense_date between gmp.month_start AND gmp.month_end
                                ) AS total_project_expense,

                                --- Compute total member by month from booking_resource_month ---
                                (SELECT 
                                        (SELECT COALESCE(NULLIF(SUM(br.man_month), NULL), 0))
                                    FROM booking_resource_month AS br
                                    LEFT JOIN planning_calendar_resource AS pl
                                        ON br.booking_id = pl.id
                                    WHERE pl.project_id = gmp.project_id
                                        AND EXTRACT (MONTH FROM br.start_date_month) = EXTRACT (MONTH FROM gmp.month_start)
                                        AND EXTRACT (YEAR FROM br.start_date_month) = EXTRACT (YEAR FROM gmp.month_start)
                                )::numeric(5, 2) AS members
                        FROM generate_month_project  AS gmp

                        GROUP BY
                            gmp.id,
                            gmp.project_id,
                            gmp.company_id,
                            gmp.month_start,
                            gmp.month_end,
                            gmp.date_start,
                            gmp.date_end,
                            gmp.project_management_id,
                            gmp.total_cost,
                            total_project_expense,
                            working_day
                        ) AS prhm
                    ),

                -- Compute average cost project, company by month ---
                project_compute_average_cost AS (
                    SELECT *,
                        --- Compute average cost project by month ---
                        (CASE 
                            WHEN expr.members = 0 OR expr.total_project_expense = 0
                                THEN expr.average_cost_company
                            ELSE (expr.average_cost_company + (expr.total_project_expense::decimal / expr.members))
                        END)::numeric(20, 4) AS average_cost_project

                    FROM (
                        SELECT *,
                            --- Compute average cost company by month ---
                            (CASE 
                                WHEN ttc.all_members = 0 
                                    THEN 0
                                ELSE ttc.operation_cost / ttc.all_members
                            END)::numeric(20, 4) AS average_cost_company

                        FROM (
                            SELECT *, (
                                    --- Compute all member by month ---
                                    SELECT SUM(members) 
                                        FROM project_compute_value_by_month AS tmp
                                    WHERE tmp.company_id = pcv.company_id
                                        AND EXTRACT (MONTH FROM pcv.month_start) = EXTRACT (MONTH FROM tmp.month_start)
                                        AND EXTRACT (YEAR FROM pcv.month_start) = EXTRACT (YEAR FROM tmp.month_start)
                                ) AS all_members
                            FROM project_compute_value_by_month AS pcv
                            GROUP BY
                                pcv.id,
                                pcv.project_id,
                                pcv.company_id,
                                pcv.date_start,
                                pcv.date_end,
                                pcv.month_start,
                                pcv.month_end,
                                pcv.project_management_id,
                                pcv.total_project_expense,
                                pcv.working_day,
                                pcv.members,
                                pcv.operation_cost,
                                all_members,
                                pcv.total_cost,
                                pcv.duration_month
                            ) AS ttc
                        ) AS expr
                ),

                --- Get data booking resource of member by month ---
                planning_by_month AS (
                    SELECT 
                        pl.project_id,
                        br.employee_id,
                        br.start_date_month,
                        br.end_date_month,
                        br.effort_rate_month,
                        br.man_month
                    FROM planning_calendar_resource AS pl
                    RIGHT JOIN booking_resource_month AS br
                        ON pl.id = br.booking_id
                    ORDER BY pl.employee_id
                ),

                --- Get data payslip of member by month ---
                payslip_by_month AS (
                    SELECT 
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        hp.contract_id,
                        hp.state,
                        hpl.total,
                        hpl.code
                    FROM hr_payslip hp
                    LEFT JOIN hr_payslip_line hpl
                        ON hp.id = hpl.slip_id
                    WHERE hpl.code IN('NET', 'NET1') AND hp.state = 'done'
                    ORDER BY hp.employee_id
                ),

                --- Merged data payslip into booking resource by month ---
                merged_planning_payslip_month AS (
                    SELECT
                        plm.project_id,
                        plm.employee_id,
                        plm.start_date_month,
                        plm.end_date_month,
                        plm.effort_rate_month,
                        plm.man_month,
                        psm.contract_id,
                        psm.state,
                        psm.total,
                        psm.code,
                        (psm.total * plm.effort_rate_month/ 100) AS salary
                    FROM planning_by_month AS plm
                    FULL JOIN payslip_by_month AS psm
                        ON plm.employee_id = psm.employee_id
                    WHERE EXTRACT (MONTH FROM plm.start_date_month) = EXTRACT (MONTH FROM psm.date_from)
                            AND EXTRACT (YEAR FROM plm.start_date_month) = EXTRACT (YEAR FROM psm.date_from)
                ),

                --- Compute total salary employee & revenue project by month ---
                project_management_compute_salary_revenue AS (
                    SELECT *, (
                            --- Compute total salary employee by month ---
                            SELECT
                                (SELECT COALESCE(NULLIF(SUM(mpp.salary), NULL), 0))
                            FROM merged_planning_payslip_month AS mpp 
                            WHERE mpp.project_id = pmh.project_id
                                AND EXTRACT (MONTH FROM mpp.start_date_month) = EXTRACT (MONTH FROM pmh.month_start)
                                AND EXTRACT (YEAR FROM mpp.start_date_month) = EXTRACT (YEAR FROM pmh.month_start)
                            )::numeric(20, 2) AS total_salary,
                        
                        --- Compute revenue by month: total_cost converted to VND from project_management ---
                        (SELECT (pmh.duration_month * pmh.total_cost) / (SELECT SUM(pmht.duration_month)
                            FROM project_compute_value_by_month AS pmht
                            WHERE pmht.project_id = pmh.project_id)
                        )::numeric(20, 4) AS revenue

                    FROM project_compute_average_cost AS pmh
                    ORDER BY pmh.project_id
                )

                SELECT *,
                    (pmc.revenue - (
                        pmc.members * pmc.average_cost_project + pmc.total_salary)
                    ) AS profit,

                    (SELECT id 
                        FROM res_currency
                        WHERE name = 'VND'
                    ) AS currency_id

                FROM project_management_compute_salary_revenue AS pmc
            )""" % (self._table)
        )
    

            