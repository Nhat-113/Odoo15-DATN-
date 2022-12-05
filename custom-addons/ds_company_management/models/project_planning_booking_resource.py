from odoo import fields, models, tools


class ProjectPlanningBookingResource(models.Model):
    _name = 'project.planning.booking'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH handle_multi_payslip AS (
                    SELECT
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        SUM(hpl.total) AS total,
                        SUM(hplbh.total) AS bhxh,
                        SUM(hpltt.total) AS ttncn
                    FROM hr_payslip AS hp
                    LEFT JOIN hr_payslip_line AS hpl
                        ON hpl.slip_id = hp.id
                        AND hpl.code IN('NET', 'NET1') 
                    LEFT JOIN hr_payslip_line AS hplbh
                        ON hp.id = hplbh.slip_id
                        AND hplbh.code = 'BH'
                    LEFT JOIN hr_payslip_line AS hpltt
                        ON hp.id = hpltt.slip_id
                        AND hpltt.code IN('TTNCN', 'TTNCN1')  
                    WHERE hp.state = 'done'
                    GROUP BY hp.employee_id,
                            hp.date_from,
                            hp.date_to
                )

                SELECT 
                    ROW_NUMBER() OVER(ORDER BY start_date_month ASC) AS id,
                    pp.company_id,
                    pl.project_id,
                    pp.department_id,
                    br.employee_id,
                    pl.member_type,
                    pmt.name AS member_type_name,
                    pl.planning_role_id,
                    date_trunc('month', br.start_date_month)::date AS months,
                    br.start_date_month,
                    br.end_date_month,
                    br.man_month,
                    br.effort_rate_month,
                    hmp.total,
                    hmp.bhxh,
                    hmp.ttncn,
                    ((COALESCE(NULLIF(hmp.total + hmp.bhxh + hmp.ttncn, NULL), 0)) * (COALESCE(NULLIF(br.effort_rate_month, NULL), 0)) / 100 ) AS salary,
                    pl.inactive,
                    pl.inactive_date,
                    pl.start_date AS start_booking,
	                pl.end_date AS end_booking
                    
                FROM booking_resource_month AS br
                LEFT JOIN planning_calendar_resource AS pl
                    ON br.booking_id = pl.id
                LEFT JOIN planning_member_type AS pmt
                    ON pmt.id = pl.member_type
                LEFT JOIN project_project AS pp
                    ON pl.project_id = pp.id
                    
                LEFT JOIN handle_multi_payslip AS hmp
                    ON hmp.employee_id = br.employee_id
                    AND EXTRACT (MONTH FROM br.start_date_month) = EXTRACT (MONTH FROM hmp.date_from)
                    AND EXTRACT (YEAR FROM br.start_date_month) = EXTRACT (YEAR FROM hmp.date_from)

                ORDER BY project_id, employee_id, months
            )""" % (self._table)
        )
        
        
        
class AvailableBookingEmployees(models.Model):
    _name = 'available.booking.employee'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
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
                get_contract_employee AS (
                    SELECT
                        hc.company_id,
                        he.department_id,
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
                                                        THEN (CONCAT('12/31/', EXTRACT(YEAR FROM hc.date_start)::text))::DATE
                                                    ELSE
                                                        (CASE
                                                            WHEN EXTRACT(MONTH FROM hc.date_start) > EXTRACT(MONTH FROM CURRENT_DATE)
                                                                THEN (CONCAT('12/31/', EXTRACT(YEAR FROM CURRENT_DATE)::text))::DATE
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
                        hct.name AS contract_type

                    FROM hr_contract AS hc
                    LEFT JOIN hr_employee AS he
                        ON he.id = hc.employee_id
                    LEFT JOIN compute_max_duration_department AS cm
                        ON cm.department_id = he.department_id
                    LEFT JOIN hr_contract_type AS hct
                        ON hct.id = hc.contract_type_id
                    WHERE hc.state != 'cancel'
                ),
                generate_contract_by_month AS (
                    SELECT
                        company_id,
                        department_id,
                        employee_id,
                    -- 	date_start,
                    -- 	date_end,
                        generate_series(
                            date_trunc('month', date_start),
                            date_trunc('month', date_end),	
                            '1 month'
                        )::date  AS months
                    FROM get_contract_employee
                    WHERE (contract_type NOT IN ('Internship', 'Intern', 'intern', 'internship') 
                                            OR contract_type IS NULL)
                    ORDER BY company_id,
                            department_id,
                            employee_id,
                            months
                ),
                generate_contract_by_month_group AS (
                    SELECT *
                    FROM generate_contract_by_month
                    GROUP BY company_id,
                            department_id,
                            employee_id,
                            months
                ),
                compute_total_payslip AS (
                    SELECT 
                        slip_id,
                    -- 	code,
                        SUM(total) AS salary
                    FROM hr_payslip_line
                    WHERE code IN ('NET', 'NET1', 'BH', 'TTNCN', 'TTNCN1')
                    GROUP BY slip_id
                    ORDER BY slip_id
                ),
                handle_multi_payslip AS (
                    SELECT
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        SUM(ctp.salary) AS salary
                    FROM hr_payslip AS hp
                    LEFT JOIN compute_total_payslip AS ctp
                        ON ctp.slip_id = hp.id
                    WHERE hp.state = 'done'
                    GROUP BY hp.employee_id,
                            hp.date_from,
                            hp.date_to
                    ORDER BY employee_id, date_from	
                ),
                compute_booking_effort_month AS (
                    SELECT
                        employee_id,
                        man_month,
                        start_date_month,
                        date_trunc('month', start_date_month)::date AS months,
                        effort_rate_month,
                        member_type_name
                    FROM project_planning_booking
                    WHERE (member_type_name NOT IN('Shadow Time', 'shadow time', 'Intern', 'intern') 
                            OR member_type_name IS NULL)
                        AND (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                            OR department_id IS NULL)
                        AND effort_rate_month > 0
                        ORDER BY employee_id, start_date_month
                ),
                compute_booking_effort_month_group AS (
                    SELECT
                        employee_id,
                        SUM(man_month) AS man_month,
                        SUM(effort_rate_month) AS effort_rate_month,
                        months
                    
                    FROM compute_booking_effort_month
                    GROUP BY employee_id,
                            months
                ),
                compute_available_salary_employee AS (
                    SELECT
                        gc.company_id,
                        gc.department_id,
                        gc.employee_id,
                        gc.months,
                        hm.salary,
                        cb.man_month,
                        cb.effort_rate_month, 
                        rc.id AS currency_id

                    FROM generate_contract_by_month_group AS gc
                    LEFT JOIN handle_multi_payslip AS hm
                        ON hm.employee_id = gc.employee_id
                        AND EXTRACT(MONTH FROM hm.date_from) = EXTRACT(MONTH FROM gc.months)
                        AND EXTRACT(YEAR FROM hm.date_from) = EXTRACT(YEAR FROM gc.months)
                    LEFT JOIN compute_booking_effort_month_group AS cb
                        ON cb.employee_id = gc.employee_id
                        AND cb.months = gc.months
                    LEFT JOIN res_currency AS rc
		                ON rc.name = 'VND'
                )
                SELECT
                    company_id,
                    department_id,
                    employee_id,
                    months,
                    (CONCAT((EXTRACT(YEAR FROM months))::text, ' ', TO_CHAR(months, 'Month'))) AS months_str,
                    salary,
                -- 		man_month,
                -- 	effort_rate_month,
                    (CASE
                        WHEN salary IS NULL
                            THEN 0
                        ELSE
                            (CASE
                                WHEN effort_rate_month IS NULL
                                    THEN salary
                                ELSE salary - (salary * effort_rate_month) / 100
                            END)
                    END) available_salary,
                    (CASE
                        WHEN effort_rate_month IS NULL
                            THEN 100
                        ELSE 100 - effort_rate_month
                    END) AS available_effort,
                    (CASE
                        WHEN man_month IS NULL
                            THEN 1
                        ELSE 1 - man_month
                    END) AS available_mm,
                    currency_id

                FROM compute_available_salary_employee
                WHERE (effort_rate_month < 100 OR effort_rate_month IS NULL)
            )""" % (self._table)
        )
        
        
class AvailableBookingEmployeeData(models.Model):
    _name = 'available.booking.employee.data'
    _order = 'employee_id'
    
    
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    months_str = fields.Char(string="Month")
    months = fields.Date(string="Month")
    salary = fields.Monetary(string='Salary')
    available_salary = fields.Monetary(string='Available Salary Cost')
    available_mm = fields.Float(string='Available MM')
    available_effort = fields.Float(string='Available Effort (%)')
    currency_id = fields.Many2one('res.currency', string="Currency")