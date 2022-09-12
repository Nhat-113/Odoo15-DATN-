from odoo import fields, models, tools
from datetime import datetime, timedelta

class ProjectManagement(models.Model):
    _name = "project.management"
    # _inherit = ['project.project']
    _description = "Project Management"
    _auto = False
    _rec_name = "project_id"


    def _compute_count_member(self):
        for record in self:
            record.count_members = len(record.member_ids)
            
    # def _compute_total_expense(self):
    #     for record in self:
    #         expenses_data = self.env['hr.expense'].search([('analytic_account_id', '=', record.get_analytic_account_id.id)])
    #         record.total_expenses = sum(expense.total_amount_company for expense in expenses_data)
            
    # def _get_expenses_last_month(self):
    #     todays = datetime.today()
    #     last_month = todays.month - 1
    #     get_year = todays.year
    #     if last_month == 0:
    #         last_month = 12
    #         get_year -= 1
            
    #     time_min_str = str(get_year) + '/' + str(last_month) + '/' + str(todays.min.day)
    #     time_max_str = str(get_year) + '/' + str(last_month) + '/' + str(todays.max.day)
    #     start_date = datetime.strptime(time_min_str, '%Y/%m/%d').date()
    #     start_end = datetime.strptime(time_max_str, '%Y/%m/%d').date()
    #     return ([('date', '>=' , start_date),('date', '<=' , start_end)])


    id = fields.Integer("ID")
    project_id = fields.Many2one('project.project', string="Project")
    director = fields.Many2one('hr.employee', string="Director")
    user_pm = fields.Many2one('res.users', string="Project Manager")
    company_id = fields.Many2one('res.company', string="Company")
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    status = fields.Char(string='Status')
    stage_id = fields.Many2one('project.task.type', string='Stage')
    
    # bonus = fields.Float(string="Bonus")
    total_cost = fields.Float(string="Revenue")
    total_effort = fields.Float(string="Total Effort(MM)")
    total_expenses = fields.Float(string="Project Cost")
    
    total_salary = fields.Float(string="Salary Cost", help="Salary Cost = SUM(salary_employee * effort_rate)")
    member_ids = fields.One2many('project.member.management', 'project_management_id', string="Members")
    project_expense_management = fields.One2many('project.expense.management', 'project_management_id', string="Project Expense Management")
    project_management_history = fields.One2many('project.management.history', 'project_management_id', string="Project Management History")
    
    count_members = fields.Integer(string='Members', compute=_compute_count_member)
    
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    pr.id,
                    pr.id AS project_id,
                    pr.analytic_account_id AS get_analytic_account_id,
                    pr.user_id AS user_pm,
                    (SELECT emp.parent_id FROM hr_employee AS emp WHERE user_id = pr.user_id) AS director,
                    pr.company_id,
                    pr.date_start,
                    pr.date AS date_end,
                    pr.last_update_status AS status,
                    pr.stage_id,
                    (SELECT count(*) FROM planning_calendar_resource AS plan WHERE plan.project_id = pr.id) AS count_employee,
                    
                    (SELECT SUM(ctr.wage * (plan.effort_rate / 100)) 
                        FROM hr_contract AS ctr 
                        Right Join planning_calendar_resource AS plan 
                            ON plan.employee_id = ctr.employee_id
                            WHERE plan.project_id = pr.id and ctr.state = 'open'
                    ) AS total_salary,
                    
                    (SELECT est.total_cost FROM estimation_work AS est WHERE est.id = pr.estimation_id) AS total_cost,
                    (SELECT res.total_effort FROM estimation_resource_effort AS res WHERE res.estimation_id = pr.estimation_id
                                                                                    and res.key_primary = 'Total (MM)') AS total_effort,
                    (SELECT SUM(pe.total_expenses) FROM project_expense_management AS pe WHERE pe.project_id = pr.id) AS total_expenses
                    
                FROM
                    project_project AS pr WHERE (EXTRACT(MONTH FROM pr.date_start) < EXTRACT(MONTH FROM CURRENT_DATE) AND
                                                EXTRACT(YEAR FROM pr.date_start) = EXTRACT(YEAR FROM CURRENT_DATE)) OR
                                                EXTRACT(YEAR FROM pr.date_start) < EXTRACT(YEAR FROM CURRENT_DATE)
                
                GROUP BY
                    pr.id,
                    pr.id,
                    pr.analytic_account_id,
                    pr.user_id,
                    director,
                    pr.company_id,
                    pr.date_start,
                    pr.date,
                    pr.last_update_status,
                    pr.stage_id,
                    count_employee,
                    total_salary,
                    total_cost,
                    total_effort,
                    total_expenses
            ) """ % (self._table)
        )

# ,
# 	                (SELECT SUM(exp.total_amount_company) 
#                         FROM hr_expense AS exp 
#                             WHERE exp.analytic_account_id = pr.analytic_account_id AND 
#                                 EXTRACT(MONTH FROM exp.date) < EXTRACT(MONTH FROM CURRENT_DATE)
#                     ) AS total_expenses
                 
                 
#                  ,
#                     total_expenses