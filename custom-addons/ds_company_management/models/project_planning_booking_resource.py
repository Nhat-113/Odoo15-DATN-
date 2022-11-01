from odoo import fields, models, tools


class ProjectPlanningBookingResource(models.Model):
    _name = 'project.planning.booking'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    ROW_NUMBER() OVER(ORDER BY start_date_month ASC) AS id,
                    pp.company_id,
                    pl.project_id,
                    pp.department_id,
		            hd.name AS department_name,
                    br.employee_id,
                    pl.member_type,
                    pmt.name AS member_type_name,
                    pl.planning_role_id,
                    date_trunc('month', br.start_date_month)::date AS months,
                    br.start_date_month,
                    br.end_date_month,
                    br.man_month,
                    br.effort_rate_month,
                    hpl.total,
	                ((COALESCE(NULLIF(hpl.total, NULL), 0)) * (COALESCE(NULLIF(br.effort_rate_month, NULL), 0)) / 100 ) AS salary,
                    pl.inactive,
                    pl.inactive_date
                    
                FROM booking_resource_month AS br
                LEFT JOIN planning_calendar_resource AS pl
                    ON br.booking_id = pl.id
                LEFT JOIN planning_member_type AS pmt
                    ON pmt.id = pl.member_type
                LEFT JOIN project_project AS pp
                    ON pl.project_id = pp.id
                LEFT JOIN hr_department AS hd
		            ON hd.id = pp.department_id
                    
                LEFT JOIN hr_payslip AS hp
                    ON hp.employee_id = br.employee_id
                    AND EXTRACT (MONTH FROM br.start_date_month) = EXTRACT (MONTH FROM hp.date_from)
                    AND EXTRACT (YEAR FROM br.start_date_month) = EXTRACT (YEAR FROM hp.date_from)
                LEFT JOIN hr_payslip_line hpl
                    ON hp.id = hpl.slip_id
                    AND hpl.code IN('NET', 'NET1') 
                    AND hp.state = 'done'
            )""" % (self._table)
        )