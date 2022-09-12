from odoo import fields, models, api, tools

class ProjectMemberManagement(models.Model):
    _name = "project.member.management"
    _description = "Project Member Management"
    _auto = False

    
    project_management_id = fields.Many2one('project.management', string="Project Management")

    employee_id = fields.Many2one('hr.employee', string="Employee") #, default=_get_member_detail
    job_id = fields.Many2one('hr.job', string="Job Position")
    email = fields.Char(string='Email')
    number_phone = fields.Char(string='Number Phone')
    salary = fields.Float(string="Salary")
    
    def init(self):
        project_managements = self.env['project.management'].search([])
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    ROW_NUMBER() OVER(ORDER BY name ASC) AS id,
                    employee.employee_id AS employee_id,
                    emp.work_email AS email,
                    emp.work_phone AS number_phone,
                    emp.job_id,
                    employee.wage salary,
                    employee.project_id AS project_management_id
                FROM hr_employee AS emp

                RIGHT JOIN (
                    SELECT
                        plan.employee_id,
                        plan.project_id,
                        (SELECT ctr.wage FROM hr_contract AS ctr WHERE ctr.employee_id = plan.employee_id AND ctr.state = 'open') AS wage
                        
                    FROM planning_calendar_resource AS plan 
                    WHERE plan.project_id IN %s
                    AND ((
                            CASE WHEN EXTRACT(MONTH FROM CURRENT_DATE) - 1 = 0 THEN 12
                                ELSE EXTRACT(MONTH FROM CURRENT_DATE) - 1
                            END)
                            BETWEEN EXTRACT(MONTH FROM plan.start_date) AND EXTRACT(MONTH FROM plan.end_date)  
                        )
                    AND ((
                            CASE WHEN EXTRACT(MONTH FROM CURRENT_DATE) - 1 = 0 THEN EXTRACT(YEAR FROM CURRENT_DATE) - 1
                                ELSE EXTRACT(YEAR FROM CURRENT_DATE)
                            END)
                            BETWEEN EXTRACT(YEAR FROM plan.start_date) AND EXTRACT(YEAR FROM plan.end_date)  
                        )
                ) AS employee 

                ON emp.id = employee.employee_id 
                GROUP BY
                    id,
                    employee_id,
                    emp.work_email,
                    emp.work_phone,
                    emp.job_id,
                    employee.wage,
                    employee.project_id
                        
            )""" % (self._table, tuple(project_managements.ids))
        )
