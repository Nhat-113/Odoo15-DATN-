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
    
    total_salary = fields.Monetary(string="Total Salary Employees", help="Total salary Employees By Month = SUM(salary_employee * effort_rate)")
    revenue = fields.Monetary(string="Revenue", help="Revenue By Month")
    profit = fields.Monetary(string="Profit")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH project_management_history_temp AS
                    (SELECT *,
                        (SELECT (SELECT COALESCE(NULLIF(SUM(eg.total_expenses), NULL), 0))
                            FROM expense_general AS eg
                            INNER JOIN expense_management AS em
                                ON eg.expense_management_id = em.id
                            WHERE em.get_month::int = EXTRACT (MONTH FROM prhm.month_start)
                                AND em.get_year::int = EXTRACT (YEAR FROM prhm.month_start)
                        ) AS operation_cost,
                        (SELECT est.total_cost
                        FROM project_project AS pr
                        INNER JOIN estimation_work AS est
                        ON est.id = pr.estimation_id
                        WHERE pr.id = prhm.project_id
                        ) AS total_cost,
                    
                        (CASE WHEN prhm.working_day >= 20 THEN 1
                        ELSE (prhm.working_day::decimal / 20)::numeric(6, 3)
                        END
                        ) AS duration_month
                    FROM
                        (SELECT  *,
                                (SELECT COUNT(*) AS working_day
                                    FROM 
                                        (SELECT dd, 
                                                EXTRACT(DOW FROM dd) AS dw
                                        FROM generate_series(ph.month_start, ph.month_end, interval '1 day') AS dd 
                                        ) AS days
                                    WHERE dw NOT IN (6,0)),

                                (SELECT ( SELECT coalesce(NULLIF(SUM(pem.total_expenses), NULL), 0))
                                    FROM project_expense_management AS pem
                                    WHERE pem.project_id = ph.project_id 
                                            AND pem.expense_date between ph.month_start AND ph.month_end
                                ) AS total_project_expense,

                                (SELECT 
                                        (SELECT COALESCE(NULLIF(SUM(br.man_month), NULL), 0))
                                    FROM booking_resource_month AS br
                                    LEFT JOIN planning_calendar_resource AS pl
                                    ON br.booking_id = pl.id
                                    WHERE EXTRACT (MONTH FROM br.start_date_month) = EXTRACT (MONTH FROM ph.month_start)
                                    AND EXTRACT (YEAR FROM br.start_date_month) = EXTRACT (YEAR FROM ph.month_start)
                                    AND pl.project_id = ph.project_id
                                )::numeric(5, 2) AS members
                        FROM (
                            SELECT 
                                ROW_NUMBER() OVER(ORDER BY months ASC) AS id,
                                phm.date_start,
                                phm.date_end,

                                (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_start) 
                                            AND EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_start)
                                    THEN phm.date_start::date
                                    ELSE phm.months::date 
                                END) AS month_start,

                                (CASE WHEN EXTRACT(MONTH FROM phm.months) = EXTRACT(MONTH FROM phm.date_end) 
                                            AND	EXTRACT(YEAR FROM phm.months) = EXTRACT(YEAR FROM phm.date_end)
                                    THEN phm.date_end::date
                                    ELSE (SELECT date_trunc('month', phm.months) + interval '1 month - 1 day')::date
                                END) AS month_end,

                                phm.project_id,
                                phm.project_management_id
                            FROM (
                                SELECT 
                                    generate_series(min, max, '1 month') AS months,
                                    pro.project_id,
                                    pro.project_management_id,
                                    pro.date_start,
                                    pro.date_end
                                FROM (
                                    SELECT date_trunc('month', min(pm.date_start)) AS min,
                                            date_trunc('month', max(pm.date_end)) AS max,
                                            pm.project_id ,
                                            pm.date_start,
                                            pm.date_end,
                                            pm.id AS project_management_id
                                    FROM project_management AS pm
                                    GROUP BY
                                        pm.project_id,
                                        pm.date_start,
                                        pm.date_end,
                                        project_management_id
                                ) AS pro
                            ) AS phm
                        ) AS ph

                        GROUP BY
                            ph.id,
                            ph.project_id,
                            ph.month_start,
                            ph.month_end,
                            ph.date_start,
                            ph.date_end,
                            ph.project_management_id,
                            total_project_expense,
                            working_day
                        ) AS prhm
                    ),

                    project_management_history_temp_ver2 AS
                    (SELECT *,
                        (CASE WHEN expr.members = 0 OR expr.total_project_expense = 0
                                    THEN expr.average_cost_company
                            ELSE (expr.average_cost_company + expr.total_project_expense::decimal / expr.members)
                        END)::numeric(20, 4) AS average_cost_project
                        
                        
                    FROM
                        (SELECT *,
                            (CASE WHEN ttc.all_members = 0 THEN 0
                                ELSE ttc.operation_cost / ttc.all_members
                            END)::numeric(20, 4) AS average_cost_company
                        FROM
                            (SELECT *,
                                (SELECT SUM(members) FROM project_management_history_temp AS tmp
                                WHERE EXTRACT (MONTH FROM pmht.month_start) = EXTRACT (MONTH FROM tmp.month_start)
                                    AND EXTRACT (YEAR FROM pmht.month_start) = EXTRACT (YEAR FROM tmp.month_start)
                                ) AS all_members
                            FROM project_management_history_temp AS pmht
                            GROUP BY
                                pmht.id,
                                pmht.project_id,
                                pmht.date_start,
                                pmht.date_end,
                                pmht.month_start,
                                pmht.month_end,
                                pmht.project_management_id,
                                pmht.total_project_expense,
                                pmht.working_day,
                                pmht.members,
                                pmht.operation_cost,
                                all_members,
                                pmht.total_cost,
                                pmht.duration_month
                            ) AS ttc
                        ) AS expr),

                    planning_by_month AS
                    (SELECT 
                        pl.project_id,
                        br.employee_id,
                        br.start_date_month,
                        br.end_date_month,
                        br.effort_rate_month,
                        br.man_month
                    FROM planning_calendar_resource AS pl
                    right join booking_resource_month AS br
                    ON pl.id = br.booking_id
                    ORDER BY pl.employee_id),

                    payslip_by_month AS
                    (SELECT 
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
                    ORDER BY hp.employee_id),

                    merged_planning_payslip_month AS
                    (SELECT
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
                    AND EXTRACT (YEAR FROM plm.start_date_month) = EXTRACT (YEAR FROM psm.date_from)),

                    project_management_history_ver3 AS
                    (SELECT *,
                        (SELECT
                            (SELECT COALESCE(NULLIF(SUM(mpp.salary), NULL), 0))
                        FROM merged_planning_payslip_month AS mpp 
                        WHERE mpp.project_id = pmh.project_id
                            AND EXTRACT (MONTH FROM mpp.start_date_month) = EXTRACT (MONTH FROM pmh.month_start)
                            AND EXTRACT (YEAR FROM mpp.start_date_month) = EXTRACT (YEAR FROM pmh.month_start)
                        )::numeric(20, 2) AS total_salary,
                    
                        ( SELECT (pmh.duration_month * pmh.total_cost * (SELECT er.usd_convert FROM api_exchange_rate AS er)) / (SELECT SUM(pmht.duration_month)
                            FROM project_management_history_temp AS pmht
                        WHERE pmht.project_id = pmh.project_id)
                        )::numeric(20, 4) AS revenue
                        
                    FROM project_management_history_temp_ver2 AS pmh
                    ORDER BY pmh.project_id)

                    SELECT *,
                    (pmhv3.revenue - (pmhv3.total_project_expense + pmhv3.average_cost_project + pmhv3.total_salary)) AS profit
                        
                    FROM project_management_history_ver3 AS pmhv3
                    
            )""" % (self._table)
        )
    
    
    @api.model
    def cron_create_history_project_management_by_month(self):
        todays = datetime.date.today()
        this_month = todays.replace(day=1)
        last_month = this_month - datetime.timedelta(days=1)
        last_month_start = last_month.replace(day=1)
        # last_month_end = last_month_start.replace(day=31)
        # months = last_month.strftime("%Y%m")
        project_managements = self.env['project.management'].search([])
        for pj in project_managements:
            expenses = self.env['hr.expense'].search([('project_management_id', '=', pj.id), ('date', '<', this_month)])
            expense_months = self.env['hr.expense'].search([('project_management_id', '=', pj.id), ('date', '>=', last_month_start), ('date', '<', this_month)])
            
            vals = {
                'project_management_id': pj.id,
                'total_expenses': sum(exp.total_amount_company for exp in expenses),
                'expense_month': sum(exp.total_amount_company for exp in expense_months),
                'month': (str(last_month.month) if last_month.month >= 10 else str(0) + str(last_month.month)) + '/' + str(last_month.year)
            }
            if vals:
                self.env['project.management.history'].create(vals)
            