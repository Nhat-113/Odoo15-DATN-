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
                    pl.inactive_date
                    
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