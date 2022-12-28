from odoo import fields, models, tools, api

class PayslipGetSalaryEmployee(models.Model):
    _name = 'payslip.get.salary.employee'
    _auto = False
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH get_salary_employee AS (
                    SELECT 
                        slip_id,
                    -- 	code,
                        SUM(total) AS salary
                    FROM hr_payslip_line
                    WHERE code IN ('NET', 'NET1', 'BH', 'BHC', 'TTNCN', 'TTNCN1', 'LTU')
                    GROUP BY slip_id
                    ORDER BY slip_id
                ),
                get_salary_13_months_overtime AS (
                    SELECT 
                        slip_id,
                        SUM(total) AS lbn_ot
                    FROM hr_payslip_line
                    WHERE code IN ('LBN', 'OT')
                    GROUP BY slip_id
                    ORDER BY slip_id
                ),

                get_slip_employee AS (
                    SELECT
                        gs.slip_id,
                        (gs.salary - gm.lbn_ot) AS salary
                    FROM get_salary_employee AS gs
                    LEFT JOIN get_salary_13_months_overtime AS gm
                        ON gm.slip_id = gs.slip_id
                )

                -- handle_multi_payslip AS (
                    SELECT
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        SUM(gs.salary) AS salary
                    FROM hr_payslip AS hp
                    LEFT JOIN get_slip_employee AS gs
                        ON gs.slip_id = hp.id
                    WHERE hp.state = 'done'
                    GROUP BY hp.employee_id,
                            hp.date_from,
                            hp.date_to           
            ) """ % (self._table)
        )
