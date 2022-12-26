from odoo import fields, models, tools


class ProjectManagementRequestOvertime(models.Model):
    _name = 'project.management.request.overtime'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH get_timesheet_overtime AS (
                    SELECT 
                        project_id,
                        employee_id,
                        unit_amount,
                        pay_type,
                    -- 	type_ot,
                        type_day_ot,
                    -- 	status_timesheet_overtime,
                        date,
                        payment_month,
                        get_year_tb
                    FROM account_analytic_line
                    WHERE status_timesheet_overtime = 'approved'
                        AND type_ot = 'yes'
                        AND ( pay_type is NOT NULL AND pay_type != 'full_day_off')
                ),
                get_bqnc_employee AS (
                    SELECT 
                        slip_id,
                        total AS bqnc
                    FROM hr_payslip_line
                    WHERE code IN ('BQNC')
                    ORDER BY slip_id
                ),
                get_payslip_duration_contract AS (
                    SELECT 
                        hp.id AS slip_id,
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                    -- 	hp.contract_id,
                        pc.starts AS start_contract,
                        pc.ends AS end_contract

                    FROM hr_payslip AS hp
                    LEFT JOIN pesudo_contract AS pc
                        ON pc.contract_id = hp.contract_id
                        AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM hp.date_from)
                        AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM hp.date_from)
                    WHERE state = 'done'
                    ORDER BY employee_id, date_from
                )

                SELECT
                    gt.project_id,
                    gt.employee_id,
                -- 	gp.start_contract,
                -- 	gp.end_contract,
                    gb.bqnc,
                    gt.date AS date_ot,
                    gt.payment_month,
	                gt.get_year_tb,
                    gt.unit_amount,
                    gt.pay_type,
                    gt.type_day_ot,
                    (CASE
                        WHEN gt.pay_type = 'full_cash'
                            THEN (CASE
                                    WHEN gt.type_day_ot = 'normal_day'
                                        THEN gt.unit_amount / 8 * gb.bqnc * 1.5
                                    WHEN gt.type_day_ot = 'weekend'
                                        THEN gt.unit_amount / 8 * gb.bqnc * 2
                                    WHEN gt.type_day_ot = 'holiday'
                                        THEN gt.unit_amount / 8 * gb.bqnc * 3
                                    ELSE gt.unit_amount / 8 * gb.bqnc
                                END)
                        -- when pay type is half cash half dayoff -> * 1/2 => 16
                        ELSE (CASE
                                WHEN gt.type_day_ot = 'normal_day'
                                    THEN gt.unit_amount / 16 * gb.bqnc * 1.5
                                WHEN gt.type_day_ot = 'weekend'
                                    THEN gt.unit_amount / 16 * gb.bqnc * 2
                                WHEN gt.type_day_ot = 'holiday'
                                    THEN gt.unit_amount / 16 * gb.bqnc * 3
                                ELSE gt.unit_amount / 16 * gb.bqnc
                            END)
                        END) AS salary,
                        pm.id AS project_management_id,
                        rc.id AS currency_id
                FROM get_bqnc_employee AS gb
                INNER JOIN get_payslip_duration_contract AS gp
                    ON gp.slip_id = gb.slip_id
                RIGHT JOIN get_timesheet_overtime AS gt
                    ON gt.employee_id = gp.employee_id
                    AND gt.date BETWEEN gp.start_contract AND gp.end_contract
                INNER JOIN project_management AS pm
	                ON pm.project_id = gt.project_id
                LEFT JOIN res_currency AS rc
	                ON rc.name = 'VND'
            ) """ % (self._table)
        )
        
        
class ProjectManagementRequestOvertimeData(models.Model):
    _name = 'project.management.request.overtime.data'
    _order = 'employee_id, date_ot DESC'
        
    project_management_id = fields.Many2one('project.management.data', string="Project Management")
    project_id = fields.Many2one('project.project', string="Project")
    currency_id = fields.Many2one('res.currency', string="Currency")
    employee_id = fields.Many2one('hr.employee', string='Employee')
    date_ot = fields.Date(string="Date")
    salary = fields.Float(string="Salary")
    unit_amount = fields.Float(string="Hours Spent")
    pay_type = fields.Selection([
                                ('full_cash', 'Full Cash'),
                                ('half_cash_half_dayoff', 'Cash 5:5 Day Off'),
                                ], string='Pay Type', index=True)
    type_day_ot = fields.Selection([
                                ('other', 'Other'),
                                ('normal_day', 'Normal Day'),
                                ('weekend', 'Weekend'),
                                ('holiday', 'Holiday'),
                                ], string='Type Day', index=True)
