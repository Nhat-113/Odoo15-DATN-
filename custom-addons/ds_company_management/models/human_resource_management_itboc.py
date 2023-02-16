from odoo import models, api,_ , tools
from odoo.http import request

class HumanResourceManagementItBoC(models.Model):
	_name = "human.resource.management.itboc"
	_description = "Human Resource IT BoC"
	_auto = False

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""
			CREATE OR REPLACE VIEW %s AS (	
                WITH get_project_boc AS (
                    SELECT
                        id,
                        company_id,
                        department_id,
                -- 		name,
                        date_start,
                        date AS date_end,
                        (COALESCE(NULLIF(total_mm, NULL), 0)) AS total_mm,
                        generate_series(
                            date_trunc('month', date_start), 
                            date_trunc('month', date), 
                            '1 month'
                        )::date AS months
                    FROM project_project 
                    WHERE project_type NOT IN (SELECT id FROM project_type WHERE name = 'Internal')
                        AND department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                ),
                compute_date_time AS (
                    SELECT
                        id,
                -- 		name,
                        company_id,
                        department_id,
                        date_start,
                        date_end,
                        total_mm,
                        months,
                        (SELECT date_trunc('month', months) + interval '1 month - 1 day')::date AS last_month,
                        (CASE WHEN EXTRACT(MONTH FROM months) = EXTRACT(MONTH FROM date_start) 
                                    AND EXTRACT(YEAR FROM months) = EXTRACT(YEAR FROM date_start)
                            THEN date_start::date
                            ELSE months
                        END) AS month_start,

                        (CASE WHEN EXTRACT(MONTH FROM months) = EXTRACT(MONTH FROM date_end) 
                                    AND EXTRACT(YEAR FROM months) = EXTRACT(YEAR FROM date_end)
                            THEN date_end::date
                            ELSE (SELECT date_trunc('month', months) + interval '1 month - 1 day')::date
                        END) AS month_end
                    FROM get_project_boc
                ),
                compute_working_day AS (
                    SELECT
                        *,
                        (SELECT COUNT(*)
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(
                                    month_start, 
                                    month_end, 
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
                                        months, 
                                        last_month, 
                                        interval '1 day'
                                    ) AS dd 
                                ) AS days
                            WHERE dw NOT IN (6,0)
                        ) AS total_working_day
                    FROM compute_date_time
                ),

                compute_man_month AS (
                    SELECT	
                        id,
                -- 		name,
                        company_id,
                        department_id,
                        months,
                        total_mm,
                        (working_day / total_working_day::DECIMAL)::NUMERIC(20, 3) AS mm
                        
                    FROM compute_working_day
                ),
                compute_total_man_month AS (
                    SELECT
                        id,
                        SUM(mm) AS mm
                    FROM compute_man_month
                    GROUP BY id
                ),

                compute_data AS (
                    SELECT
                        mm.id AS project_id,
                    -- 	mm.name,
                        mm.company_id,
                        mm.department_id,
                    -- 	mm.months,
                        (EXTRACT(YEAR FROM mm.months)) AS years,
                        (EXTRACT(MONTH FROM mm.months)) AS months,
                        mm.total_mm,
                    -- 	(mm.mm * total_mm / ct.mm) AS mm
                        (CASE
                            WHEN ct.mm != 0
                                THEN mm.mm * total_mm / ct.mm
                            ELSE 0
                        END)::NUMERIC(20, 3) AS mm,
                        ru.id AS representative,
                        hd.manager_id 

                    FROM compute_man_month AS mm
                    LEFT JOIN compute_total_man_month AS ct
                        ON ct.id = mm.id
                    LEFT JOIN hr_department AS hd
                        ON hd.id = mm.department_id
                    LEFT JOIN res_company AS rc
                        ON rc.id = mm.company_id
                    LEFT JOIN res_users AS ru
                        ON ru.login = rc.user_email
                )

                SELECT
                    company_id,
                    department_id,
                    years,
                    months,
                    SUM(mm) AS mm,
                    manager_id,
                    representative
                    
                FROM compute_data
                GROUP BY company_id,
                        department_id,
                        years,
                        months,
                        manager_id,
                        representative
                ORDER BY company_id, department_id, years, months

            )""" % (self._table)
		)