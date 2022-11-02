from odoo import fields, models, tools


class ProjectManagementCeo(models.Model):
    _name = 'project.management.ceo'
    _description = 'Project Management CEO'
    _auto = False
    
    
    def init(self):
        department_ids = self.env['project.management'].handle_remove_department()
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH cost_management_subceo_group AS (
                    SELECT 
                        pms.company_id,
                        pms.month_start,
                        pms.month_end,
                        (SUM(pms.total_members)) AS total_members,
                        (SUM(pms.total_salary)) AS total_salary,
                        (SUM(pms.total_project_cost)) AS total_project_cost,
                        (SUM(pms.total_revenue)) AS total_revenue,
                        (SUM(pms.total_profit)) AS total_profit,
                        pms.currency_id
                        
                    FROM project_management_subceo AS pms
                    GROUP BY pms.company_id,
                            pms.month_start,
                            pms.month_end,
                            pms.currency_id
                ),
                
                handling_datetime_company_history AS (
                    SELECT
                        hch.id,
                        hch.company_id,
                        hch.representative AS old_manager_id,
                        (CASE
                            WHEN hch.date_start IS NULL
                                THEN '1/1/2021'::date
                            ELSE
                                hch.date_start::date
                        END) AS date_start,
                        
                        (CASE
                            WHEN hch.date_end IS NULL
                                THEN (date_trunc('month', CURRENT_DATE::DATE) + interval '1 month - 1 day')::date
                            ELSE
                                hch.date_end::date
                        END) AS date_end
                    FROM hr_company_history AS hch
                ),
                history_manager_company AS (
                    SELECT
                        rc.id AS company_id,
                        he.id AS manager_id,
                        hdc.old_manager_id,
                        hdc.date_start,
                        hdc.date_end,
                        generate_series(
                                date_trunc('month', 
                                        (CASE
                                            --- When manager is expired ---
                                            WHEN hdc.date_start IS NOT NULL
                                                    THEN hdc.date_start::date
                                            ELSE '1/1/2021'::date
                                        END)
                                ), 
                                date_trunc('month', 
                                        (CASE
                                            --- When manager is expired ---
                                            WHEN hdc.date_end IS NOT NULL
                                                    THEN hdc.date_end::date
                                            ELSE (CURRENT_DATE::DATE - interval '1 month')
                                        END)
                                
                                ),	
                                '1 month'
                        )::date  AS months
                        
                    FROM res_company AS rc
                    LEFT JOIN handling_datetime_company_history AS hdc
                        ON hdc.company_id = rc.id
                    LEFT JOIN hr_employee AS he
                        ON rc.user_email = he.work_email
                ),

                history_company_gen_month AS (
                    SELECT
                        hmc.company_id,
                        hmc.manager_id,
                        hmc.old_manager_id,
                        hmc.months,
                        (CASE 
                            WHEN EXTRACT(MONTH FROM hmc.months) = EXTRACT(MONTH FROM hmc.date_start) 
                                    AND EXTRACT(YEAR FROM hmc.months) = EXTRACT(YEAR FROM hmc.date_start)
                                THEN hmc.date_start::date
                            ELSE hmc.months
                        END) AS month_start,

                        (CASE 
                            WHEN EXTRACT(MONTH FROM hmc.months) = EXTRACT(MONTH FROM hmc.date_end) 
                                    AND	EXTRACT(YEAR FROM hmc.months) = EXTRACT(YEAR FROM hmc.date_end)
                                THEN hmc.date_end::date
                            ELSE (SELECT date_trunc('month', hmc.months) + interval '1 month - 1 day')::date
                        END) AS month_end,
                                
                        (SELECT date_trunc('month', hmc.months) + interval '1 month - 1 day')::date AS month_end_date
                        
                    FROM history_manager_company AS hmc
                ),

                compute_working_day_manager AS (
                    SELECT
                        hc.company_id,
                        hc.manager_id,
                        hc.old_manager_id,
                        hc.month_start,
                        hc.month_end,
                        hc.months AS month_start_date,
                        hc.month_end_date,
                        
                        (SELECT COUNT(*)
                            FROM (
                                SELECT dd, 
                                        EXTRACT(DOW FROM dd) AS dw
                                FROM generate_series(
                                            hc.month_start, 
                                            hc.month_end, 
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
                                            hc.months, 
                                            hc.month_end_date, 
                                            interval '1 day'
                                ) AS dd 
                            ) AS days
                            
                            WHERE dw NOT IN (6,0)
                        ) AS working_day_total
                        
                    FROM history_company_gen_month AS hc
                ),

                get_salary_manager_company AS (
                    SELECT
                        cw.company_id,
                        cw.manager_id,
                        cw.old_manager_id,
                        cw.month_start,
                        cw.month_end,
                        cw.month_start_date,
                        cw.month_end_date,
                        cw.working_day,
                        cw.working_day_total,
                        hpl.total,
                        hpll.total AS bqnc
                    FROM compute_working_day_manager AS cw
                    LEFT JOIN hr_payslip AS hp
                        ON (CASE
                                WHEN cw.old_manager_id IS NULL
                                    THEN hp.employee_id = cw.manager_id
                                ELSE
                                    hp.employee_id = cw.old_manager_id
                            END)
                        AND EXTRACT(MONTH FROM hp.date_from) = EXTRACT(MONTH FROM cw.month_start)
                        AND EXTRACT(YEAR FROM hp.date_from) = EXTRACT(YEAR FROM cw.month_start)
                        
                    LEFT JOIN hr_payslip_line AS hpl
                            ON hpl.slip_id = hp.id
                            AND hpl.code IN('NET', 'NET1') AND hp.state = 'done'
                    LEFT JOIN hr_payslip_line AS hpll
                            ON hpll.slip_id = hp.id
                            AND hpll.code IN('BQNC') AND hp.state = 'done'

                ),
                
                project_planning_booking_remove_department_fnb AS (
                    SELECT
                        employee_id,
                        man_month,
                        start_date_month,
                        effort_rate_month
                    FROM project_planning_booking
                    WHERE department_id NOT IN %s
                ),

                compute_salary_subceo AS (
                    SELECT 
                        cms.company_id,
                    -- 	gs.manager_id,
                    -- 	gs.old_manager_id,
                        (CASE
                            WHEN gs.old_manager_id IS NOT NULL
                                THEN gs.old_manager_id
                            ELSE
                                gs.manager_id
                        END) AS manager,
                    -- 	gs.month_start AS month_start_manager,
                    -- 	gs.month_end AS month_end_manager,
                    -- 	rcm.months as month_start_date,
                    -- 	gs.month_end_date,
                        cms.month_start,
                        cms.month_end,
                    -- 	gs.working_day,
                    -- 	gs.working_day_total,
                    -- 	gs.total,
                    -- 	gs.bqnc,
                    -- 	ppb.effort_rate_month,
                    -- 	ppb.man_month,
                        
                    -- 	mdh.manager_id AS manager_department,
                    -- 	mdh.manager_history_id AS old_manager_department,
                        cms.total_revenue,
                        cms.total_members,
                        cms.total_salary,
                        cms.total_project_cost,
                        cms.total_profit,
                        -- 	calculate members Manager company ---
                        (CASE
                            -- 	when manager company is a manager department
                            WHEN mdh.manager_id IS NOT NULL OR mdh.manager_history_id IS NOT NULL
                                THEN 0
                            ELSE
                                (CASE
                                    -- when manager company doesn't join project ---
                                    WHEN ppb.man_month IS NULL
                                        THEN (gs.working_day::NUMERIC(10,5) / gs.working_day_total)
                                    ELSE
                                        (gs.working_day::NUMERIC(10,5) / gs.working_day_total) - ppb.man_month
                                END)
                        END) AS remaining_members,
                        
                        (CASE
                            WHEN mdh.manager_id IS NOT NULL OR mdh.manager_history_id IS NOT NULL
                                THEN (CASE
                                        -- when manager company is manager department and doesn't join project but only work for half a month ---
                                        WHEN mdh.working_day <> mdh.working_day_total AND mdh.effort_rate_month IS NULL
                                            THEN
                                                COALESCE(NULLIF(mdh.salary_manager, NULL), 0) - (COALESCE(NULLIF(mdh.bqnc, NULL), 0) * mdh.working_day)
                                        ELSE
                                            0
                                    END)
                            ELSE
                                (CASE
                                    --- when the manager quits in the middle of the month ---
                                    WHEN gs.working_day <> gs.working_day_total
                                        THEN (CASE
                                                WHEN ppb.effort_rate_month IS NULL
                                                    THEN COALESCE(NULLIF(gs.bqnc, NULL), 0) * gs.working_day
                                                ELSE
                                                    COALESCE(NULLIF(gs.bqnc, NULL), 0) * gs.working_day * (100 - ppb.effort_rate_month) / 100
                                            END)
                                    ELSE
                                        (CASE
                                            WHEN ppb.effort_rate_month IS NULL
                                                THEN COALESCE(NULLIF(gs.total, NULL), 0)
                                            ELSE
                                                COALESCE(NULLIF(gs.total, NULL), 0) * (100 - ppb.effort_rate_month) / 100
                                        END)
                                END)
                        END) AS remaining_salary

                    FROM cost_management_subceo_group AS cms
                    LEFT JOIN get_salary_manager_company AS gs
                        ON gs.company_id = cms.company_id
                        AND gs.month_start_date = cms.month_start
                    LEFT JOIN project_planning_booking_remove_department_fnb AS ppb
                        ON (CASE
                                WHEN gs.old_manager_id IS NOT NULL
                                    THEN gs.old_manager_id = ppb.employee_id
                                ELSE
                                    gs.manager_id = ppb.employee_id
                            END)

                        AND EXTRACT(MONTH FROM gs.month_start_date) = EXTRACT(MONTH FROM ppb.start_date_month)
                        AND EXTRACT(YEAR FROM gs.month_start_date) = EXTRACT(YEAR FROM ppb.start_date_month)
                    LEFT JOIN manager_department_history AS mdh
                        ON (CASE
                                WHEN mdh.manager_history_id IS NOT NULL
                                    THEN (CASE
                                            WHEN gs.old_manager_id IS NOT NULL
                                                THEN mdh.manager_history_id = gs.old_manager_id
                                            ELSE
                                                mdh.manager_history_id = gs.manager_id
                                        END)
                                ELSE
                                    (CASE
                                        WHEN gs.old_manager_id IS NOT NULL
                                            THEN mdh.manager_id = gs.old_manager_id
                                        ELSE
                                            mdh.manager_id = gs.manager_id
                                    END)
                            END)
                        AND EXTRACT(MONTH FROM mdh.month_start) = EXTRACT(MONTH FROM cms.month_start)
                        AND EXTRACT(YEAR FROM mdh.month_start) = EXTRACT(YEAR FROM cms.month_start)

                        ORDER BY company_id, gs.manager_id, month_start
                ),

                remove_department_record_superfluous AS (
                    SELECT
                        css.company_id,
                        css.manager,
                        css.month_start,
                        css.month_end,
                        css.total_revenue,
                        css.total_members,
                        css.total_salary,
                        css.total_project_cost,
                        css.total_profit,
                        css.remaining_members,
                        css.remaining_salary
                    FROM compute_salary_subceo AS css
                    GROUP BY

                        css.company_id,
                        css.manager,
                        css.month_start,
                        css.month_end,
                        css.total_revenue,
                        css.total_members,
                        css.total_project_cost,
                        css.total_salary,
                        css.total_profit,
                        css.remaining_members,
                        css.remaining_salary
                ),
                cost_management_final AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                        company_id,
                        month_start,
                        month_end,
                        total_revenue,
                        total_project_cost,
                        (total_members + SUM(remaining_members)) AS total_members,
                        (total_salary + SUM(remaining_salary)) AS total_salary,
                        (total_profit - SUM(remaining_salary)) AS total_profit

                    FROM remove_department_record_superfluous AS rd
                    GROUP BY
                        company_id,
                        month_start,
                        month_end,
                        total_revenue,
                        total_members,
                        total_project_cost,
                        total_salary,
                        total_profit
                )
                
                SELECT
                    cm.id,
                    cm.company_id,
                    he.id AS representative,
                    (CONCAT((EXTRACT(YEAR FROM cm.month_start))::text, ' ', TO_CHAR(cm.month_start, 'Month'))) AS months,
                    cm.month_start,
                    cm.month_end,
                    cm.total_revenue,
                    cm.total_members,
                    cm.total_project_cost,
                    cm.total_salary,
                    cm.total_profit,
                    rcu.id AS currency_id
                FROM cost_management_final AS cm
                LEFT JOIN res_company AS rc
                    ON rc.id = cm.company_id
                LEFT JOIN hr_employee AS he
                    ON he.work_email = rc.user_email
                LEFT JOIN res_currency AS rcu
	                ON rcu.name = 'VND'
            ) """ % (self._table, tuple(department_ids))
        )
        
    
class ProjectManagementCeoData(models.Model):
    _name = 'project.management.ceo.data'
    _description = 'Project Management CEO Data'
    
    
    company_id = fields.Many2one('res.company', string='Company')
    representative = fields.Many2one('hr.employee', string='Representative')
    months = fields.Char(string="Month")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    total_members = fields.Float(string='Effort(MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_project_cost = fields.Float(string="Project Cost")
    total_revenue = fields.Float(string="Revenue")
    total_profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2))
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    def get_department_management_detail(self):
        action = {
            'name': self.company_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management.subceo.data',
            'view_ids': self.env.ref('ds_company_management.project_management_subceo_action').id,
            'view_mode': 'tree',
            'domain': [('month_start', '=', self.month_start), ('company_id', '=', self.company_id.id)]
        }
        return action