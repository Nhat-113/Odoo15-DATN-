from odoo import fields, models, tools, api


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
                    company_id,
                    (date_trunc('month', month_start))::date AS month_start,
                    average_cost_company
                FROM project_management_history
                GROUP BY company_id,
                    date_trunc('month', month_start)::date,
                    average_cost_company
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
                        --company_id,
                        --department_id,
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
                    GROUP BY --company_id,
                        --department_id,
                        employee_id,
                        months
                    ORDER BY employee_id, months
                ),
                get_contract_employee AS (
                    SELECT 
                        company_id,
                        department_id,
                        employee_id,
                        months,
                        SUM(working_day) AS working_day,
                        total_working_day,
                        type_contract
                        
                    FROM pesudo_contract
                    GROUP BY company_id,
                            department_id,
                            employee_id,
                            months,
                            total_working_day,
                            type_contract
                ),

                compute_available_effort_employee AS (
                    SELECT
                        he.company_id AS company_emp,
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
                                        THEN gc.working_day / gc.total_working_day * (100 - ct.effort_rate_month) / 100
                                    ELSE 1 - ct.man_month
                                END)
                        END)::NUMERIC(10, 2) AS available_mm,
                        
                        -- Handle member have multi contract of multi company in a month
                        (CASE
                            WHEN ct.effort_rate_month IS NULL
                                THEN (CASE
                                        WHEN gc.working_day <> gc.total_working_day
                                            THEN gc.working_day / gc.total_working_day * 100
                                        ELSE 100
                                    END)
                            ELSE (CASE
                                    WHEN gc.working_day <> gc.total_working_day
                                        THEN ((100 - ct.effort_rate_month) * gc.working_day / 100) / gc.total_working_day * 100
                                    ELSE 100 - ct.effort_rate_month
                                END)
                        END)::NUMERIC(20, 2) AS available_effort,
                        
                        --ct.man_month,
                        --ct.effort_rate_month,
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
                    LEFT JOIN res_currency AS rc
                        ON rc.name = 'VND'
                    LEFT JOIN hr_employee AS he
		                ON he.id = gc.employee_id

                    ORDER BY department_id, employee_id, months
                ),
                compute_available_salary_employee AS (
                    SELECT
                        ca.company_emp,
                        ca.company_id,
                        ca.department_id,
                        ca.employee_id,
                        ca.months,
                        ca.available_mm,
                        ca.available_effort,
                        ca.average_cost_company,
                        
                        (CASE
                            WHEN hm.salary IS NULL
                                THEN 0
                            ELSE (hm.salary + COALESCE(NULLIF(pc.salary_lbn, NULL), 0)) * ca.available_effort / 100
                        END)::NUMERIC(20, 4) AS available_salary,
                        ca.type_contract,
                        ca.currency_id

                    FROM compute_available_effort_employee AS ca
                    LEFT JOIN payslip_get_salary_employee AS hm
                        ON hm.employee_id = ca.employee_id
                        AND EXTRACT (MONTH FROM ca.months) = EXTRACT (MONTH FROM hm.date_from)
                        AND EXTRACT (YEAR FROM ca.months) = EXTRACT (YEAR FROM hm.date_from)
                    LEFT JOIN pesudo_contract_generate AS pc
                        ON pc.employee_id = ca.employee_id
                        AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM ca.months)
                        AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM ca.months)
                )
                SELECT
                    company_emp,
                    company_id,
                    department_id,
                    employee_id,
                    months,
                    (CONCAT((EXTRACT(YEAR FROM months))::text, ' ', TO_CHAR(months, 'Month'))) AS months_str,
                    SUM(available_mm) AS available_mm,
                    SUM(available_effort) AS available_effort,
                -- 	salary,
                    SUM(available_salary) AS available_salary,
                -- 	average_cost_company,
                    SUM(CASE
                            WHEN type_contract = 'intern'
                                THEN 0
                            ELSE average_cost_company * available_mm
                        END) AS available_operation,
                    currency_id
                -- 	type_contract
                    

                FROM compute_available_salary_employee
                WHERE available_effort > 0
                GROUP BY company_emp, 
                        company_id,
                        department_id,
                        employee_id,
                        months,
                        available_effort,
                        available_salary,
                -- 		salary,
                        currency_id
                        

                ORDER BY  employee_id, months
            )""" % (self._table)
        )
        
        
class AvailableBookingEmployeeData(models.Model):
    _name = 'available.booking.employee.data'
    _order = 'company_id, department_id, employee_id, months DESC'
    
    
    company_emp = fields.Many2one('res.company', string='Company Employee')
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
    
    
    
class ComparePayslipContract(models.Model):
    _name = 'compare.payslip.contract'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    hc.id AS contract_id,
                    hp.company_id AS company_payslip,
                    hc.company_id AS company_contract,
                    hp.employee_id AS employee_payslip,
                    hc.employee_id AS employee_contract,
                    hp.date_from,
                    hp.date_to,
                    hp.state,
                    hc.date_start,
                    hc.date_end
                FROM hr_payslip AS hp
                FULL JOIN hr_contract AS hc
                ON hc.id = hp.contract_id
            ) """ % (self._table)
        )


class ComparePayslipContractData(models.Model):
    _name = 'compare.payslip.contract.data'
    _order = 'company_payslip, employee_payslip, date_from DESC'
    
    contract_id = fields.Many2one('hr.contract', string='Contract')
    company_payslip = fields.Many2one('res.company', string='Company Payslip')
    company_contract = fields.Many2one('res.company', string='Company Contract')
    employee_payslip = fields.Many2one('hr.employee', string='Employee Payslip')
    employee_contract = fields.Many2one('hr.employee', string='Employee Contract')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    date_start = fields.Date(string='Start Contract')
    date_end = fields.Date(string='End Contract')
    state = fields.Selection([
                                ('draft', 'Draft'),
                                ('verify', 'Waiting'),
                                ('done', 'Done'),
                                ('cancel', 'Rejected'),
                            ], string='Status', index=True)
    
    
    @api.model
    def upgrade_compare_payslip_contract_support(self):
        user_update = str(self.env.user.id)
        query = self.query_compare_payslip_contract_support(user_update)
        self.env.cr.execute(query)
        return
        
    def query_compare_payslip_contract_support(self, user_update):
        return """
                DELETE FROM compare_payslip_contract_data;
                INSERT INTO 
                    compare_payslip_contract_data(
                        contract_id,
                        company_payslip,
                        company_contract,
                        employee_payslip,
                        employee_contract,
                        date_from,
                        date_to,
                        date_start,
                        date_end,
                        state,
                        create_uid, 
                        write_uid, 
                        create_date, 
                        write_date
                    )  
                SELECT 
                    contract_id,
                    company_payslip,
                    company_contract,
                    employee_payslip,
                    employee_contract,
                    date_from,
                    date_to,
                    date_start,
                    date_end,
                    state,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM compare_payslip_contract;
            """