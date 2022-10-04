from odoo import fields, models, tools


class ProjectManagementSubCeo(models.Model):
    _name = 'project.management.subceo'
    _description = 'Project Management Sub CEO'
    _auto = False
    _order = "id desc"
    
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    total_members = fields.Float(string='Members', digits=(12,3))
    total_salary = fields.Monetary(string="Salary Cost")
    total_project_cost = fields.Monetary(string="Project Cost")
    total_revenue = fields.Monetary(string="Revenue")
    total_profit = fields.Monetary(string="Profit")
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    user_login = fields.Many2one('res.users', string="User")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                --- Generate month, history of department from '1/1/2021' to last month ---
                WITH department_by_month AS (
                    SELECT
                    generate_series(
                                date_trunc('month', '1/1/2021'::date), 
                                date_trunc('month', CURRENT_DATE - interval '1 month'),
                                '1 month'
                        )::date AS months,
                        hd.id AS department_id,
                        hd.manager_id,
                        hd.company_id
                        
                        FROM hr_department AS hd
                ),

                --- Check if the department manager is a project manager ---
                merged_department_booking_resource_month AS (
                    SELECT
                        dbm.company_id,
                        dbm.department_id,
                        dbm.manager_id,
                        dbm.months,
                        brm.effort_rate_month AS effort_rate_month_manager,
                        brm.man_month AS man_month_manager
                FROM department_by_month AS dbm
                LEFT JOIN booking_resource_month AS brm
                    ON dbm.manager_id = brm.employee_id
                    AND EXTRACT(MONTH FROM dbm.months) = EXTRACT(MONTH FROM brm.start_date_month)
                    AND EXTRACT(YEAR FROM dbm.months) = EXTRACT(YEAR FROM brm.start_date_month)
                ),

                --- Get department, company from project management to project management history ---
                project_history_department AS (
                    SELECT
                            pm.company_id,
                            pm.department_id,
                            (date_trunc('month', pmh.month_start))::date AS month_start,
                            pmh.members,
                            pmh.total_project_expense AS project_cost,
                            pmh.profit,
                            pmh.total_salary AS salary_cost,
                            pmh.revenue,
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

                merged_department_history_month AS (
                    SELECT
                            dbm.company_id,
                            dbm.department_id,
                            dbm.manager_id,
                            dbm.months AS month_start,
                            
                            (SELECT 
                                date_trunc('month', dbm.months) + interval '1 month - 1 day'
                            )::date AS month_end,
                            
                            COALESCE(NULLIF(phdg.members,		NULL), 0)  AS total_members,
                            COALESCE(NULLIF(phdg.project_cost,	NULL), 0)  AS total_project_cost,
                            COALESCE(NULLIF(phdg.revenue, 		NULL), 0)  AS total_revenue,
                            COALESCE(NULLIF(phdg.salary_cost, 	NULL), 0)  AS total_salary,
                            COALESCE(NULLIF(phdg.profit, 		NULL), 0)  AS total_profit,
                            COALESCE(
                                NULLIF(phdg.currency_id, NULL), 
                                        (SELECT id FROM res_currency 
                                            WHERE name = 'VND')
                            )  AS currency_id,
                            phdg.average_cost_company,
                            dbm.effort_rate_month_manager,
                            dbm.man_month_manager
                            
                            
                    FROM merged_department_booking_resource_month AS dbm
                    LEFT JOIN project_history_department_group as phdg
                        ON dbm.company_id = phdg.company_id
                        AND dbm.department_id = phdg.department_id
                        AND dbm.months = phdg.month_start
                                                                
                ),

                hr_payslip_payroll AS (
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
                ),

                merged_compute_department_history_payroll AS (
                    SELECT
                            ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                            mdhm.company_id,
                            mdhm.department_id,
                            mdhm.manager_id,
                            mdhm.month_start,
                            mdhm.month_end,
                            
                            --- Compute member with manager ---
                            (CASE
                                WHEN mdhm.man_month_manager IS NOT NULL
                                    THEN (CASE
                                            WHEN mdhm.total_members + (1 - mdhm.man_month_manager) < 0
                                                THEN 0
                                            ELSE
                                                mdhm.total_members + (1 - mdhm.man_month_manager)
                                        END)
                                ELSE (CASE
                                        WHEN mdhm.manager_id IS NULL
                                            THEN mdhm.total_members
                                        ELSE
                                            mdhm.total_members + 1
                                    END)
                            END) AS total_members,
                            
                            --- compute salary with manager ---
                            (CASE
                                WHEN hpp.total IS NULL
                                    THEN mdhm.total_salary
                                ELSE (CASE
                                        WHEN mdhm.effort_rate_month_manager IS NULL
                                            THEN mdhm.total_salary + hpp.total
                                            
                                        --- case when manager join project ---
                                        ELSE mdhm.total_salary + hpp.total - (hpp.total * mdhm.effort_rate_month_manager / 100 )
                                    END)
                            END) AS total_salary,
                            
                            (CASE
                                WHEN hpp.total IS NULL
                                    THEN mdhm.total_profit
                                ELSE (CASE
                                        WHEN mdhm.effort_rate_month_manager IS NULL
                                            THEN mdhm.total_profit - hpp.total
                                                
                                        --- case when manager join project ---
                                        ELSE mdhm.total_profit - (hpp.total - (hpp.total * mdhm.effort_rate_month_manager / 100 ))
                                    END)
							END)::NUMERIC(20, 4) AS total_profit,
                            
                            mdhm.total_project_cost,
                            mdhm.total_revenue,
                            mdhm.average_cost_company,
                            hpp.total AS salary_manager,
                            mdhm.effort_rate_month_manager,
                            mdhm.man_month_manager,
			                mdhm.currency_id
                            
                            
                    FROM merged_department_history_month AS mdhm
                    LEFT JOIN hr_payslip_payroll AS hpp
                        ON mdhm.manager_id = hpp.employee_id
                        AND EXTRACT(MONTH FROM mdhm.month_start) = EXTRACT(MONTH FROM hpp.date_from)
                        AND EXTRACT(YEAR FROM mdhm.month_start) = EXTRACT(YEAR FROM hpp.date_from)
                )
                
                SELECT
                    mcd.id,
                    mcd.company_id,
                    mcd.department_id,
                    mcd.manager_id,
                    mcd.month_start,
                    mcd.month_end,
                    mcd.total_members,
                    mcd.total_salary,
                    mcd.total_profit,
                    mcd.total_project_cost,
                    mcd.total_revenue,
                    mcd.average_cost_company,
                    mcd.salary_manager,
                    mcd.effort_rate_month_manager,
                    mcd.man_month_manager,
                    mcd.currency_id,
                    ru.id AS user_login
                    
                FROM merged_compute_department_history_payroll AS mcd
                LEFT JOIN res_company AS rc
                    ON rc.id = mcd.company_id
                LEFT JOIN res_users AS ru
                    ON ru.login = rc.user_email
            ) """ % (self._table)
        )
        
        
    
        
    def get_project_detail(self):
        action = {
            'name': self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'department.project.detail',
            'view_ids': self.env.ref('ds_company_management.department_project_detail_action').id,
            'view_mode': 'tree',
            'domain': [('department_id', '=', self.department_id.id), 
                       ('company_id', '=', self.company_id.id),
                       ('month_start', 'in', [self.month_start, self.month_end])]
        }
        return action