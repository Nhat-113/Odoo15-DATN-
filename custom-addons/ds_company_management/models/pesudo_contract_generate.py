from odoo import fields, models, tools

class PesudoContract(models.Model):
    _name = 'pesudo.contract'
    _auto = False
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH compute_max_duration_company AS (
                    SELECT
                        (CASE
                            WHEN max(sort_date) < CURRENT_DATE::DATE
                                THEN (date_trunc('month', CURRENT_DATE) + interval '1 month - 1 day')::DATE
                            ELSE (date_trunc('month', max(sort_date)) + interval '1 month - 1 day')::DATE
                        END) AS max_months,
                        pp.company_id
                    FROM project_revenue_value AS prv
                    LEFT JOIN project_project AS pp
                        ON pp.id = prv.project_id
                    GROUP BY pp.company_id
                ),

                get_contract_employee_company AS (
                    SELECT
                        hc.company_id,
                        hc.department_id,
                        hc.employee_id,
                        hc.date_start,
                        (CASE
                            WHEN hc.date_end IS NULL
                                THEN
                                    (CASE
                                        WHEN cm.max_months IS NULL
                                            THEN 
                                                (CASE
                                                    WHEN EXTRACT(YEAR FROM hc.date_start) > EXTRACT(YEAR FROM CURRENT_DATE)
                                                        THEN to_date(CONCAT('12 31 ', EXTRACT(YEAR FROM hc.date_start)::text), 'MM DD YYYY')
                                                    ELSE
                                                        (CASE
                                                            WHEN EXTRACT(MONTH FROM hc.date_start) > EXTRACT(MONTH FROM CURRENT_DATE)
                                                                THEN to_date(CONCAT('12 31 ', EXTRACT(YEAR FROM CURRENT_DATE)::text), 'MM DD YYYY')
                                                            ELSE (date_trunc('month', CURRENT_DATE::DATE) + interval '1 month - 1 day')::date
                                                        END)
                                                END)
                                        ELSE 
                                            (CASE
                                                WHEN EXTRACT(YEAR FROM hc.date_start) > EXTRACT(YEAR FROM cm.max_months)
                                                    THEN hc.date_start
                                                ELSE (cm.max_months + interval '1 month - 1 day')::date
                                            END)
                                    END)
                            ELSE hc.date_end
                        END) AS date_end,
                        hc.contract_document_type,
                        hc.id AS contract_id

                    FROM hr_contract AS hc
                    LEFT JOIN compute_max_duration_company AS cm
                        ON cm.company_id = hc.company_id
                    
                    --LEFT JOIN hr_employee AS he
                        --ON he.id = hc.employee_id
                    WHERE hc.state != 'cancel'
                ),

                generate_month_contract_company AS (
                    SELECT
                        company_id,
                        department_id,
                        employee_id,
                        generate_series(
                            date_trunc('month', min(date_start)), 
                            date_trunc('month', max(date_end)), 
                            '1 month'
                        )::date AS months,
                        date_start,
                        date_end,
                        contract_document_type,
                        contract_id
                    
                    FROM get_contract_employee_company
                    WHERE department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                            OR department_id IS NULL
                    GROUP BY company_id, department_id, employee_id, date_start, date_end, contract_document_type, contract_id
                    ORDER BY department_id, employee_id, months
                ),
                get_start_end_month_contract AS (
                    SELECT
                        company_id,
                        department_id,
                        employee_id,
                        months,
                        (CASE
                            WHEN EXTRACT(MONTH FROM months) = EXTRACT(MONTH FROM date_start)
                                AND EXTRACT(YEAR FROM months) = EXTRACT(YEAR FROM date_start)
                                THEN date_start
                            ELSE months
                        END) AS starts,
                        
                        (CASE
                            WHEN EXTRACT(MONTH FROM months) = EXTRACT(MONTH FROM date_end)
                                AND EXTRACT(YEAR FROM months) = EXTRACT(YEAR FROM date_end)
                                THEN date_end
                            ELSE (date_trunc('month', months) + interval '1 month - 1 day')::date
                        END) AS ends,
                        contract_document_type,
                        contract_id
                    -- 	date_start,
                    -- 	date_end
                    FROM generate_month_contract_company
                )
                SELECT
                    company_id,
                    department_id,
                    employee_id,
                    months,
                    starts,
                    ends,
                    (SELECT COUNT(*)
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(
                                    starts, 
                                    ends, 
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
                                    (date_trunc('month', months) + interval '1 month - 1 day')::DATE, 
                                    interval '1 day'
                                ) AS dd 
                            ) AS days
                        WHERE dw NOT IN (6,0)
                    ) AS total_working_day,
                    contract_document_type,
                    (CASE
                        WHEN contract_document_type NOT IN('Intern', 'intern', 'internship')
                            THEN 'official'
                        ELSE 'intern'
                    END) AS type_contract,
                    contract_id
                FROM get_start_end_month_contract
                
            ) """ % (self._table)
        )


class PesudoContractGenerate(models.Model):
    _name = 'pesudo.contract.generate'
    _auto = False
    _description = "Model is used to calculate salary 13 months member"
    
    
    # Model is calculate salary 13 months member
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH compute_working_day_month_contract AS (
                    SELECT
                        employee_id,
                        months,
                        SUM(working_day::DECIMAL / total_working_day::DECIMAL)::NUMERIC(10, 2) AS mm,
                        EXTRACT(YEAR FROM months) AS years
                    FROM pesudo_contract
                    WHERE contract_document_type = 'offical_labor'
                    GROUP BY employee_id, months
                ),
                compute_total_month_contract AS (
                    SELECT
                        employee_id,
                        years,
                        SUM(mm) AS total_mm
                    FROM compute_working_day_month_contract
                    GROUP BY employee_id, years
                ),

                get_salary_lbn AS (
                    SELECT
                        hp.employee_id,
                        EXTRACT(YEAR FROM hp.date_from) AS years,
                        SUM(hpl.total) AS total
                    FROM hr_payslip_line AS hpl
                    INNER JOIN hr_payslip AS hp
                        ON hp.id = hpl.slip_id
                    WHERE hpl.code = 'LBN' AND hp.state = 'done'
                    GROUP BY hp.employee_id, EXTRACT(YEAR FROM hp.date_from) 
                    ORDER BY employee_id
                )

                SELECT
                    cw.employee_id,
                    cw.months,
                    --cw.mm,
                    cw.years,
                    --ct.total_mm,
                    --gs.total,
                    --(COALESCE(NULLIF(gs.total * mm / total_mm, NULL), 0) / ) AS salary_lbn
                    (CASE
                        WHEN gs.total IS NULL OR cw.mm IS NULL OR ct.total_mm IS NULL OR ct.total_mm = 0
                            THEN 0
                        ELSE gs.total * cw.mm / ct.total_mm
                    END) salary_lbn

                FROM compute_working_day_month_contract AS cw
                LEFT JOIN compute_total_month_contract AS ct
                    ON ct.employee_id = cw.employee_id
                    AND ct.years = cw.years
                LEFT JOIN get_salary_lbn AS gs
                    ON gs.employee_id = cw.employee_id
                    AND gs.years = cw.years
            ) """ % (self._table)
        )