from odoo import fields, models, tools


class ProjectManagementMemberDetail(models.Model):
    _name = 'project.management.member.detail'
    _auto = False
    
    employee_id = fields.Many2one('hr.employee', string="Employee")
    role_ids = fields.Many2one('config.job.position', string='Roles')
    currency_id = fields.Many2one('res.currency', string="Currency")
    member_type = fields.Many2one('planning.member.type', string='Member Type')
    
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    effort_rate = fields.Float(string="Effort Rate(%)")
    working_day = fields.Float(string="Working day")
    man_month = fields.Float(string="Man month")
    total_members = fields.Float(string="Members project", digits=(12,3))
    
    average_cost_company = fields.Float(string="Average Cost Company")
    average_cost_project = fields.Float(string="Average Cost Project")
    
    salary = fields.Monetary(string="Salary")
    profit = fields.Monetary(string="Profit")
    average_profit = fields.Monetary(string="Average profit")
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    project_members = fields.Many2one('project.management.member', string="Project members")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    ROW_NUMBER() OVER(ORDER BY brm.start_date_month) AS id,
                    pmm.id AS project_members,
                    pcr.employee_id,
                    brm.start_date_month AS month_start,
                    brm.end_date_month AS month_end,
                    (SELECT COUNT(*)
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(
                                    brm.start_date_month, 
                                    brm.end_date_month, 
                                    interval '1 day'
                                ) AS dd 
                            ) AS days
                        WHERE dw NOT IN (6,0)
                    ) AS working_day,
                    brm.effort_rate_month AS effort_rate,
                    brm.man_month,
                    -- 	brm.member_type,
                    -- 	pcr.role_ids,
                    -- 	pcr.inactive,
                    -- 	pcr.inactive_date,
                    pmh.average_cost_company,
                    pmh.average_cost_project,
                    pmh.profit,
                    pmh.members_project_not_intern AS total_members,
                    
                    (CASE
                        WHEN pmt.name IN('intern', 'Intern')
                            THEN 0
                        ELSE hpl.total * brm.effort_rate_month
                    END) AS salary,
                    
                    (CASE
                        WHEN pmt.name IN('intern', 'Intern')
                            THEN 0
                        ELSE 
                            (CASE
                                WHEN pmh.members_project_not_intern = 0 OR pmh.members_project_not_intern IS NULL 
                                    OR pmh.profit = 0 OR pmh.profit IS NULL
                                    THEN 0
                                ELSE pmh.profit / pmh.members_project_not_intern * brm.effort_rate_month / 100
                            END)
                    END) AS average_profit,
                    
                    pmh.currency_id
                    
                    -- 	esc.types,
                    -- 	esc.yen_day,
                    -- 	esc.yen_month,
                    -- 	ew.currency_id as est_currency,
                    -- 	ec.name AS est_currency_name,
                    -- 	hpl.total,
                    -- hpl.code
                    
                    
                FROM booking_resource_month AS brm
                LEFT JOIN planning_calendar_resource AS pcr
                    ON pcr.id = brm.booking_id

                LEFT JOIN project_management_member AS pmm
                    ON pmm.employee_id = pcr.employee_id
                    AND pmm.project_id = pcr.project_id
                    
                LEFT JOIN planning_member_type AS pmt
	                ON pmt.id = pmm.member_type

                LEFT JOIN project_management_history AS pmh
                    ON pmh.project_id = pcr.project_id
                    AND EXTRACT(MONTH FROM pmh.month_start) = EXTRACT(MONTH FROM brm.start_date_month) 
                    AND EXTRACT(YEAR FROM pmh.month_start) = EXTRACT(YEAR FROM brm.start_date_month) 
                    
                --- Get salary from payroll ---
                LEFT JOIN hr_payslip AS hp
                    ON hp.employee_id = pcr.employee_id
                    AND EXTRACT(MONTH FROM hp.date_from) = EXTRACT(MONTH FROM brm.start_date_month) 
                    AND EXTRACT(YEAR FROM hp.date_from) = EXTRACT(YEAR FROM brm.start_date_month)
                LEFT JOIN hr_payslip_line AS hpl
                    ON hpl.slip_id = hp.id
                    AND hpl.code IN('NET', 'NET1') AND hp.state = 'done'
                    

                --- Get estimation ---
                -- LEFT JOIN project_project AS pp
                -- 	ON pp.id = pcr.project_id
                -- LEFT JOIN estimation_work AS ew
                -- 	ON ew.id = pp.estimation_id
                -- LEFT JOIN estimation_currency AS ec
                -- 	ON ec.id = ew.currency_id

                --- Get cost by role from estimation_summary_costrate ---
                -- LEFT JOIN config_job_position AS cjp
                -- 	ON cjp.id = pcr.role_ids
                -- LEFT JOIN estimation_summary_costrate AS esc
                -- 	ON esc.connect_summary_costrate = pp.estimation_id
                -- 	AND esc.types = cjp.job_position

            )""" % (self._table)
        )