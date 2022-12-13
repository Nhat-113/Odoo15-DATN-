from odoo import fields, models, tools


class ProjectManagementMemberDetail(models.Model):
    _name = 'project.management.member.detail'
    _auto = False
    _order = 'month_start desc'

    
    
    def init(self):
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
                    --pmh.members_project_not_intern AS total_members,
                    pmh.members AS total_members,
                    ppb.salary,
                    (CONCAT((EXTRACT(YEAR FROM ppb.start_date_month))::text, ' ', TO_CHAR(ppb.start_date_month, 'Month'))) AS months,
                    
                    (CASE
                        WHEN pmh.members = 0 OR pmh.members IS NULL 
                            OR pmh.profit = 0 OR pmh.profit IS NULL
                            THEN 0
                        ELSE pmh.profit / pmh.members * ppb.effort_rate_month / 100
                    END) AS average_profit,
                    
                    pmh.currency_id
                    
                FROM project_planning_booking AS ppb
                RIGHT JOIN project_management_member AS pmm
                    ON pmm.employee_id = ppb.employee_id
                    AND pmm.project_id = ppb.project_id
                    AND ppb.start_booking BETWEEN pmm.start_date AND pmm.end_date
	                AND ppb.end_booking BETWEEN pmm.start_date AND pmm.end_date
                    
                LEFT JOIN planning_member_type AS pmt
                    ON pmt.id = pmm.member_type

                LEFT JOIN project_management_history AS pmh
                    ON pmh.project_id = ppb.project_id
                    AND EXTRACT(MONTH FROM pmh.month_start) = EXTRACT(MONTH FROM ppb.start_date_month) 
                    AND EXTRACT(YEAR FROM pmh.month_start) = EXTRACT(YEAR FROM ppb.start_date_month) 
                    
                WHERE ppb.department_id NOT IN (SELECT department_id FROM department_mirai_fnb) 
                    OR ppb.department_id IS NULL

            )""" % (self._table)
        )
        
        
class ProjectManagementMemberDetailData(models.Model):
    _name = 'project.management.member.detail.data'
    _order = 'month_start desc'
    
    
        
    employee_id = fields.Many2one('hr.employee', string="Employee")
    currency_id = fields.Many2one('res.currency', string="Currency")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    effort_rate = fields.Float(string="Effort Rate (%)")
    working_day = fields.Float(string="Working day")
    man_month = fields.Float(string="Man month")
    total_members = fields.Float(string="Effort (MM)", digits=(12,3))
    months = fields.Char(string="Month")
    
    average_cost_company = fields.Float(string="Company Avg Cost")
    average_cost_project = fields.Float(string="Prj Avg Cost")
    
    salary = fields.Monetary(string="Salary")
    profit = fields.Monetary(string="Profit")
    average_profit = fields.Monetary(string="Avg profit")
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    project_members = fields.Many2one('project.management.member', string="Project members")
    