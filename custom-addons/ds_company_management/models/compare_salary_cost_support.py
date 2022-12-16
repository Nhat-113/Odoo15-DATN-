from odoo import fields, models, tools, api

class CompareSalaryCostSupport(models.Model):
    _name = 'compare.salary.cost'
    _auto = False
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH get_payslip_line_value AS (
                    SELECT 
                        slip_id,
                        total,
                        code
                    FROM hr_payslip_line
                    WHERE code IN ('NET', 'NET1', 'BH', 'TTNCN', 'TTNCN1', 'LBN')
                ),
                compute_salary_value AS (
                    SELECT 
                        hp.company_id,
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        (net.total - lbn.total) AS salary,
                        bh.total AS bhxh,
                        tt.total AS ttncn,
                -- 		lbn.total AS salary_lbn,
                        --pc.salary_lbn,
                        --COALESCE(NULLIF(pc.salary_lbn, NULL), 0) AS salary_lbn,
                        rc.id AS currency_id
                    FROM hr_payslip AS hp
                    LEFT JOIN get_payslip_line_value AS net
                        ON net.slip_id = hp.id
                        AND net.code IN ('NET', 'NET1')
                    LEFT JOIN get_payslip_line_value AS bh
                        ON bh.slip_id = hp.id
                        AND bh.code = 'BH'
                    LEFT JOIN get_payslip_line_value AS tt
                        ON tt.slip_id = hp.id
                        AND tt.code IN ('TTNCN', 'TTNCN1')
                    LEFT JOIN get_payslip_line_value AS lbn
                        ON lbn.slip_id = hp.id
                        AND lbn.code = 'LBN'
                    --LEFT JOIN pesudo_contract_generate AS pc
                        --ON pc.employee_id = hp.employee_id
                        --AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM hp.date_from)
                        --AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM hp.date_from)
                    LEFT JOIN res_currency AS rc
		                ON rc.name = 'VND'
                    WHERE hp.state = 'done'
                    ORDER BY company_id, employee_id, date_from
                )
                -- Handle multi payslip
                SELECT
                    company_id,
                    employee_id,
                    date_trunc('month', date_from)::DATE AS months,
                    date_from,
                    date_to,
                    SUM(salary) AS salary,
                    SUM(bhxh) AS bhxh,
                    SUM(ttncn) AS ttncn,
                    --salary_lbn,
                    currency_id
                FROM compute_salary_value
                GROUP BY company_id,
                        employee_id,
                        date_from,
                        date_to,
                        --salary_lbn,
                        currency_id                
            ) """ % (self._table)
        )


class CompareSalaryCostData(models.Model):
    _name = 'compare.salary.cost.data'
    _order = 'company_id, employee_id, date_from DESC'
    
    
    company_id = fields.Many2one('res.company', string='Company')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    months = fields.Date(string='Months Filter')
    date_from = fields.Date(string='Date from')
    date_to = fields.Date(string='Date to')
    salary = fields.Monetary(string="Salary")
    bhxh = fields.Monetary(string="BHXH")
    ttncn = fields.Monetary(string='TTNCN')
    # salary_lbn = fields.Monetary(string='13th Month Salary')
    total_salary = fields.Monetary(string='Total Salary Cost')
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    
    @api.model
    def upgrade_salary_cost_support(self):
        user_update = str(self.env.user.id)
        query = self.query_compare_salary_cost(user_update)
        self.env.cr.execute(query)
        return
        
    def query_compare_salary_cost(self, user_update):
        return """
                DELETE FROM compare_salary_cost_data;
                INSERT INTO 
                    compare_salary_cost_data(
                        company_id,
                        currency_id,
                        employee_id,
                        months,
                        date_from,
                        date_to,
                        salary,
                        bhxh,
                        ttncn,
                        --salary_lbn,
                        total_salary,
                        create_uid, 
                        write_uid, 
                        create_date, 
                        write_date
                    )  
                SELECT 
                    company_id,
                    currency_id,
                    employee_id,
                    months,
                    date_from,
	                date_to,
                    salary,
                    bhxh,
                    ttncn,
                    --salary_lbn,
                    (salary + bhxh + ttncn) AS total_salary,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM compare_salary_cost;
            """