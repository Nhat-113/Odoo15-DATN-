from odoo import fields, models, tools


class ProjectManagementMemberDetail(models.Model):
    _name = 'project.management.member.detail'
    _auto = False
    _order = 'month_start desc'

    
    
    def init(self):
        department_ids = self.env['project.management'].handle_remove_department()
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    ROW_NUMBER() OVER(ORDER BY ppb.id ASC) AS id,
                    pmm.id AS project_members,
                    ppb.employee_id,
                    ppb.start_date_month AS month_start,
                    ppb.end_date_month AS month_end,
                    (SELECT COUNT(*)
                        FROM (
                            SELECT dd, 
                                    EXTRACT(DOW FROM dd) AS dw
                            FROM generate_series(
                                    ppb.start_date_month, 
                                    ppb.end_date_month, 
                                    interval '1 day'
                                ) AS dd 
                            ) AS days
                        WHERE dw NOT IN (6,0)
                    ) AS working_day,
                    ppb.effort_rate_month AS effort_rate,
                    ppb.man_month,
                    pmh.average_cost_company,
                    pmh.average_cost_project,
                    pmh.profit,
                    pmh.members_project_not_intern AS total_members,
                    (CONCAT((EXTRACT(YEAR FROM ppb.start_date_month))::text, ' ', TO_CHAR(ppb.start_date_month, 'Month'))) AS months,
                    
                    (CASE
                        WHEN pmt.name IN('intern', 'Intern')
                            THEN 0
                        ELSE hpl.total * ppb.effort_rate_month / 100
                    END) AS salary,
                    
                    (CASE
                        WHEN pmt.name IN('intern', 'Intern')
                            THEN 0
                        ELSE 
                            (CASE
                                WHEN pmh.members_project_not_intern = 0 OR pmh.members_project_not_intern IS NULL 
                                    OR pmh.profit = 0 OR pmh.profit IS NULL
                                    THEN 0
                                ELSE pmh.profit / pmh.members_project_not_intern * ppb.effort_rate_month / 100
                            END)
                    END) AS average_profit,
                    
                    pmh.currency_id
                    
                FROM project_planning_booking AS ppb

                RIGHT JOIN project_management_member AS pmm
                    ON pmm.employee_id = ppb.employee_id
                    AND pmm.project_id = ppb.project_id
                    
                LEFT JOIN planning_member_type AS pmt
                    ON pmt.id = pmm.member_type

                LEFT JOIN project_management_history AS pmh
                    ON pmh.project_id = ppb.project_id
                    AND EXTRACT(MONTH FROM pmh.month_start) = EXTRACT(MONTH FROM ppb.start_date_month) 
                    AND EXTRACT(YEAR FROM pmh.month_start) = EXTRACT(YEAR FROM ppb.start_date_month) 
                    
                --- Get salary from payroll ---
                LEFT JOIN hr_payslip AS hp
                    ON hp.employee_id = ppb.employee_id
                    AND EXTRACT(MONTH FROM hp.date_from) = EXTRACT(MONTH FROM ppb.start_date_month) 
                    AND EXTRACT(YEAR FROM hp.date_from) = EXTRACT(YEAR FROM ppb.start_date_month)
                LEFT JOIN hr_payslip_line AS hpl
                    ON hpl.slip_id = hp.id
                    AND hpl.code IN('NET', 'NET1') AND hp.state = 'done'
                WHERE ppb.department_id NOT IN %s
                ORDER BY project_members, employee_id

            )""" % (self._table, tuple(department_ids))
        )
        
        
class ProjectManagementMemberDetailData(models.Model):
    _name = 'project.management.member.detail.data'
    _order = 'month_start desc'
    
    
        
    employee_id = fields.Many2one('hr.employee', string="Employee")
    currency_id = fields.Many2one('res.currency', string="Currency")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    effort_rate = fields.Float(string="Effort Rate(%)")
    working_day = fields.Float(string="Working day")
    man_month = fields.Float(string="Man month")
    total_members = fields.Float(string="Effort(MM)", digits=(12,3))
    months = fields.Char(string="Month")
    
    average_cost_company = fields.Float(string="Company Avg Cost")
    average_cost_project = fields.Float(string="Prj Avg Cost")
    
    salary = fields.Monetary(string="Salary")
    profit = fields.Monetary(string="Profit")
    average_profit = fields.Monetary(string="Avg profit")
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    project_members = fields.Many2one('project.management.member', string="Project members")
    