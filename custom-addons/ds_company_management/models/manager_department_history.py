from odoo import fields, models, tools


class ManagerDepartmentHistory(models.Model):
    _name = 'manager.department.history'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                --- compute max duration for generate month for department by revenue management of company expense
                WITH compute_max_duration_department AS (
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

                handling_datetime_department_history AS (
                    SELECT
                        hdh.id,
                        hdh.department_id,
                        hdh.manager_history_id,
                        (CASE
                            WHEN hdh.date_start IS NULL
                                THEN '1/1/2021'::date
                            ELSE
                                hdh.date_start::date
                        END) AS date_start,
                        
                        (CASE
                            WHEN hdh.date_end IS NULL
                                THEN (CASE
                                        WHEN cm.max_months IS NULL
                                            THEN (date_trunc('month', CURRENT_DATE::DATE) + interval '1 month - 1 day')::date
                                        ELSE (cm.max_months + interval '1 month - 1 day')::date
                                    END)
                            ELSE
                                hdh.date_end::date
                        END) AS date_end
                    FROM hr_department_history AS hdh
                    LEFT JOIN compute_max_duration_department AS cm
                        ON cm.department_id = hdh.department_id
                ),

                history_manager_department AS (
                    SELECT
                        hd.company_id,
                        hd.id AS department_id,
                        hd.manager_id,
                        hdh.manager_history_id,
                        hdh.date_start,
                        hdh.date_end,
                    
                        generate_series(
                                date_trunc('month',
                                    (CASE
                                        --- When manager is expired ---
                                        WHEN hdh.date_start IS NOT NULL
                                            THEN hdh.date_start::date
                                        ELSE '1/1/2021'::date
                                    END)
                                ),
                                date_trunc('month',
                                    (CASE
                                        --- When manager is expired ---
                                        WHEN hdh.date_end IS NOT NULL
                                            THEN hdh.date_end::date
                                        WHEN cm.max_months IS NOT NULL
                                            THEN cm.max_months
                                        ELSE CURRENT_DATE::DATE
                                    END)
                            
                                ),	
                                '1 month'
                            )::date  AS months
                        
                    FROM hr_department AS hd
                    LEFT JOIN handling_datetime_department_history AS hdh
                        ON hd.id = hdh.department_id
                    LEFT JOIN compute_max_duration_department AS cm
                        ON cm.department_id = hd.id
                    WHERE hd.id NOT IN (SELECT department_id FROM department_mirai_fnb)
                ),

                history_department_gen_month AS (
                    SELECT
                        *,
                        
                        (CASE WHEN EXTRACT(MONTH FROM hmd.months) = EXTRACT(MONTH FROM hmd.date_start) 
                                    AND EXTRACT(YEAR FROM hmd.months) = EXTRACT(YEAR FROM hmd.date_start)
                            THEN hmd.date_start::date
                            ELSE hmd.months
                        END) AS month_start,

                        (CASE WHEN EXTRACT(MONTH FROM hmd.months) = EXTRACT(MONTH FROM hmd.date_end) 
                                    AND	EXTRACT(YEAR FROM hmd.months) = EXTRACT(YEAR FROM hmd.date_end)
                            THEN hmd.date_end::date
                            ELSE (SELECT date_trunc('month', hmd.months) + interval '1 month - 1 day')::date
                        END) AS month_end,
                            
                        (date_trunc('month', hmd.months) + interval '1 month - 1 day')::date AS month_end_date

                    FROM history_manager_department AS hmd
                ),

                compute_working_day AS (
                    SELECT
                        hdgm.company_id,
                        hdgm.department_id,
                        hdgm.manager_id,
                        hdgm.manager_history_id,
                        hdgm.month_start,
                        hdgm.month_end,
                        hdgm.months AS month_start_date,
                        hdgm.month_end_date,

                        (SELECT COUNT(*)
                            FROM (
                                SELECT dd, 
                                        EXTRACT(DOW FROM dd) AS dw
                                FROM generate_series(
                                        hdgm.month_start, 
                                        hdgm.month_end, 
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
                                        hdgm.months, 
                                        hdgm.month_end_date, 
                                        interval '1 day'
                                ) AS dd 
                            ) AS days
                            WHERE dw NOT IN (6,0)
                        ) AS working_day_total
                        
                    FROM history_department_gen_month AS hdgm
                    
                ),

                get_salary_manager AS (
                    SELECT 
                        cw.company_id,
                        cw.department_id,
                        cw.manager_id,
                        cw.manager_history_id,
                        cw.month_start,
                        cw.month_end,
                        cw.month_start_date,
                        cw.month_end_date,
                        cw.working_day,
                        cw.working_day_total,
                        hpl.total,
                        hpll.total AS bqnc
                        
                    FROM compute_working_day AS cw
                    LEFT JOIN hr_payslip AS hp
                        ON (CASE
                                WHEN cw.manager_history_id IS NULL
                                    THEN hp.employee_id = cw.manager_id
                                ELSE
                                    hp.employee_id = cw.manager_history_id
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
                    WHERE department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                        OR department_id IS NULL
                )

                SELECT
                    gsm.company_id,
                    gsm.department_id,
                    gsm.manager_id,
                    gsm.manager_history_id,
                    gsm.month_start,
                    gsm.month_end,
                    gsm.working_day,
                    gsm.working_day_total,
                    gsm.bqnc,
                    gsm.total AS salary_manager,
                    ppb.effort_rate_month,
                    ppb.man_month
                FROM get_salary_manager AS gsm
                LEFT JOIN project_planning_booking_remove_department_fnb AS ppb
                -- LEFT JOIN booking_resource_month AS brm
                    ON (CASE
                            WHEN gsm.manager_history_id IS NOT NULL
                                THEN gsm.manager_history_id = ppb.employee_id
                            ELSE
                                gsm.manager_id = ppb.employee_id
                        END)

                    AND EXTRACT(MONTH FROM gsm.month_start) = EXTRACT(MONTH FROM ppb.start_date_month)
                    AND EXTRACT(YEAR FROM gsm.month_start) = EXTRACT(YEAR FROM ppb.start_date_month)

            )""" % (self._table)
        )