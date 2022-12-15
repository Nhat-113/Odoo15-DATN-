from odoo import fields, models, tools


class ProjectHistoryGroup(models.Model):
    _name = 'project.history.group.temp'
    _auto = False
    _description = 'Model support calculate total fields from Cost Management'
    
    project_management_id = fields.Many2one('project.management', string="Project Management")
    company_id = fields.Many2one('res.company', string="Company")
    project_id = fields.Many2one('project.project', string="Project")
    total_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_profit = fields.Float(string="Profit")
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    project_id AS id,
                    project_id,
                    SUM(members) AS total_members,
                    SUM(total_salary) AS total_salary,
                    SUM(total_project_expense) AS total_project_expense,
                    SUM(total_department_expense) AS total_department_expense,
                    SUM(profit) AS total_profit,
                    SUM(total_avg_operation_project) AS total_avg_operation_project

                FROM project_management_history
                GROUP BY project_id
            ) """ % (self._table)
        )
        
        
class AverageCostCompany(models.Model):
    _name = 'average.cost.company.temp'
    _auto = False
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    pm.company_id,
                    (date_trunc('month', pmh.month_start))::date AS month_start,
                    pmh.average_cost_company
                FROM project_management AS pm
                RIGHT JOIN project_management_history AS pmh
                    ON pm.id = pmh.project_management_id
                GROUP BY pm.company_id,
                    month_start,
                    pmh.average_cost_company
            ) """ % (self._table)
        )
        

      
class AvailableBookingEmployees(models.Model):
    _name = 'available.booking.employee'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                ---- Compute available_booking_employee --
                WITH compute_total_effort_by_month AS (
                    SELECT 
                        company_id,
                        department_id,
                        employee_id,
                        months,
                        SUM(man_month) AS man_month,
                        SUM(effort_rate_month) AS effort_rate_month
                -- 		SUM(salary) AS salary
                    FROM project_planning_booking
                    WHERE (member_type_name NOT IN('Shadow Time', 'shadow time') 
                            OR member_type_name IS NULL)
                        AND (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                            OR department_id IS NULL)
                        AND effort_rate_month > 0
                    GROUP BY company_id,
                        department_id,
                        employee_id,
                        months
                    ORDER BY department_id, employee_id, months
                ),
                get_contract_employee AS (
                    SELECT 
                        company_id,
                        department_id,
                        employee_id,
                        months,
                        SUM(working_day) AS working_day,
                        total_working_day,
                        
                        (CASE
                            WHEN contract_document_type NOT IN('Intern', 'intern', 'internship')
                                THEN 'official'
                            ELSE 'intern'
                        END) AS type_contract
                        
                    FROM pesudo_contract
                    GROUP BY company_id,
                            department_id,
                            employee_id,
                            months,
                            total_working_day,
                            type_contract
                ),

                get_salary_employee AS (
                    SELECT 
                        slip_id,
                    -- 	code,
                        SUM(total) AS salary
                    FROM hr_payslip_line
                    WHERE code IN ('NET', 'NET1', 'BH', 'TTNCN', 'TTNCN1')
                    GROUP BY slip_id
                    ORDER BY slip_id
                ),

                get_salary_13_months AS (
                    SELECT 
                        slip_id,
                        total
                    FROM hr_payslip_line
                    WHERE code IN ('LBN')
                    ORDER BY slip_id
                ),

                get_payslip_employee AS (
                    SELECT
                        gs.slip_id,
                        (gs.salary - gm.total) AS salary
                    FROM get_salary_employee AS gs
                    LEFT JOIN get_salary_13_months AS gm
                        ON gm.slip_id = gs.slip_id
                ),

                handle_multi_payslip AS (
                    SELECT
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        SUM(gs.salary) AS salary
                    FROM hr_payslip AS hp
                    LEFT JOIN get_payslip_employee AS gs
                        ON gs.slip_id = hp.id
                    WHERE hp.state = 'done'
                    GROUP BY hp.employee_id,
                            hp.date_from,
                            hp.date_to
                ),

                compute_available_effort_employee AS (
                    SELECT
                        gc.company_id,
                        gc.department_id,
                        gc.employee_id,
                        gc.months,
                        gc.working_day,
                        gc.total_working_day,
                        (CASE
                            WHEN ct.effort_rate_month IS NULL
                                THEN (CASE
                                        WHEN gc.working_day <> gc.total_working_day
                                            THEN gc.working_day / gc.total_working_day 
                                        ELSE 1
                                    END)
                            ELSE (CASE
                                    WHEN gc.working_day <> gc.total_working_day
                                        THEN 1 - gc.working_day / gc.total_working_day * ct.effort_rate_month / 100
                                    ELSE 1 - ct.man_month
                                END)
                        END) AS available_mm,
                        
                        (CASE
                            WHEN ct.effort_rate_month IS NULL
                                THEN 100
                            ELSE 100 - ct.effort_rate_month
                        END) AS available_effort,
                        
                        (CASE
                            WHEN hm.salary IS NULL
                                THEN 0
                            ELSE (CASE
                                    WHEN ct.effort_rate_month IS NULL
                                        THEN hm.salary + COALESCE(NULLIF(pc.salary_lbn, NULL), 0)
                                    ELSE (hm.salary + COALESCE(NULLIF(pc.salary_lbn, NULL), 0)) * (100 - ct.effort_rate_month) / 100
                                END)
                        END) AS available_salary,
                -- 		hm.salary,
                -- 		pc.salary_lbn,
                                
                        ct.man_month,
                        ct.effort_rate_month,
                -- 		(COALESCE(NULLIF(ct.salary, NULL), 0)) AS salary,
                        (COALESCE(NULLIF(ac.average_cost_company, NULL), 0)) AS average_cost_company,
                        gc.type_contract,
                        rc.id AS currency_id

                    FROM get_contract_employee AS gc
                    LEFT JOIN compute_total_effort_by_month AS ct
                        ON --ct.company_id = gc.company_id
                        --AND ct.department_id = gc.department_id
                        --AND 
                            ct.employee_id = gc.employee_id
                        AND ct.months = gc.months
                    LEFT JOIN average_cost_company_temp AS ac
                        ON ac.company_id = gc.company_id
                        AND ac.month_start = gc.months
                    LEFT JOIN handle_multi_payslip AS hm
                        ON hm.employee_id = gc.employee_id
                        AND EXTRACT (MONTH FROM gc.months) = EXTRACT (MONTH FROM hm.date_from)
                        AND EXTRACT (YEAR FROM gc.months) = EXTRACT (YEAR FROM hm.date_from)
                    LEFT JOIN pesudo_contract_generate AS pc
                    ON pc.employee_id = gc.employee_id
                    AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM gc.months)
                    AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM gc.months)
                    LEFT JOIN res_currency AS rc
                        ON rc.name = 'VND'

                    ORDER BY department_id, employee_id, months
                )
                SELECT
                    company_id,
                    department_id,
                    employee_id,
                    months,
                    (CONCAT((EXTRACT(YEAR FROM months))::text, ' ', TO_CHAR(months, 'Month'))) AS months_str,
                    SUM(available_mm) AS available_mm,
                    available_effort,
                -- 	salary,
                    available_salary,
                -- 	average_cost_company,
                    SUM(CASE
                            WHEN type_contract = 'intern'
                                THEN 0
                            ELSE average_cost_company * available_mm
                        END) AS available_operation,
                    currency_id
                -- 	type_contract
                    

                FROM compute_available_effort_employee
                WHERE available_effort > 0
                GROUP BY company_id,
                        department_id,
                        employee_id,
                        months,
                        available_effort,
                        available_salary,
                -- 		salary,
                        currency_id
                        

                ORDER BY department_id, employee_id, months
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
    available_salary = fields.Monetary(string='Salary Cost')
    available_mm = fields.Float(string='Effort (MM)')
    available_effort = fields.Float(string='Effort Rate (%)')
    available_operation = fields.Float(string='Operation Cost')
    currency_id = fields.Many2one('res.currency', string="Currency")