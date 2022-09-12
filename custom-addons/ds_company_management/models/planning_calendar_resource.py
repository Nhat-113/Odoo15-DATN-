from odoo import api, models, fields, tools



class PlanningCalendarResource(models.Model):
    _name = "planning.calendar.resource.month"
    _auto = False
    _rec_name = "project_id"
    
    project_id = fields.Many2one('project.project', string="Project")
    employee_id = fields.Many2one('hr.employee', string="Employee")
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    working_day = fields.Integer(string="Working Day")
    effort_rate = fields.Float(string="Effort Rate")
    
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ple.project_id,
                    ple.employee_id,
                    ple.month_start::date,
                    ple.month_end::date,
                    (SELECT count(*) AS working_day
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(ple.month_start, ple.month_end, interval '1 day') AS dd 
                        ) AS days
                        WHERE dw NOT IN (6, 0)
                    ),
                    ple.effort_rate
                FROM
                    (SELECT emp.project_id,
                            emp.employee_id,
                            emp.effort_rate,

                            (CASE WHEN EXTRACT(MONTH FROM emp.month_start) = EXTRACT(MONTH FROM emp.start_date) 
                                    THEN emp.start_date
                                    ELSE emp.month_start
                            END) AS month_start,
                            (CASE WHEN EXTRACT (MONTH FROM (SELECT date_trunc('month', emp.month_start) + interval '1 month - 1 day'))
                                                = EXTRACT(MONTH FROM emp.end_date) 
                            THEN emp.end_date
                            ELSE 
                                (SELECT date_trunc('month', emp.month_start) + interval '1 month - 1 day') 
                            END) as month_end
                    FROM
                        (SELECT 
                            generate_series(min, max, '1 month') AS month_start,
                            pro.project_id,
                            pro.employee_id,
                            pro.start_date,
                            pro.end_date,
                            pro.effort_rate
                        FROM 
                            (SELECT date_trunc('month', min(pl.start_date)) AS min,
                                    date_trunc('month', max(pl.end_date)) AS max,
                            pl.project_id,
                            pl.employee_id,
                            pl.start_date,
                            pl.end_date,
                            pl.effort_rate
                            FROM planning_calendar_resource AS pl
                            GROUP BY
                                pl.project_id,
                                pl.employee_id,
                                pl.start_date,
                                pl.end_date,
                                pl.effort_rate
                            )
                        AS pro) 
                    AS emp)
                AS ple
            ) """ % (self._table)
        )