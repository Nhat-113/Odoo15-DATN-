from odoo import fields, models, tools


class ProjectPlanningBookingResource(models.Model):
    _name = 'project.planning.booking'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH get_slip_employee AS (
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
                        SUM(gs.salary) AS salary
                    FROM hr_payslip AS hp
                    LEFT JOIN get_slip_employee AS gs
                        ON gs.slip_id = hp.id
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
                    ((COALESCE(NULLIF(hmp.salary + pc.salary_lbn, NULL), 0)) * (COALESCE(NULLIF(br.effort_rate_month, NULL), 0)) / 100 ) AS salary,
                    pc.salary_lbn,
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
                LEFT JOIN pesudo_contract_generate AS pc
                    ON pc.employee_id = br.employee_id
                    AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM br.start_date_month)
                    AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM br.start_date_month)

                ORDER BY project_id, employee_id, months
            )""" % (self._table)
        )
        
        