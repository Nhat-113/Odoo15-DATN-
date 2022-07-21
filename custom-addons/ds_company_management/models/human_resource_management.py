from datetime import date
from odoo import fields, models


class HumanResourceManagement(models.Model):
    _name = "human.resource.management"
    _description = "Human Resource Management"
    _auto = False

    id = fields.Many2one('hr.employee', string="ID", readonly=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", readonly=True)
    name = fields.Char(string="Employee Name", readonly=True)
    work_phone = fields.Char(string="Work Phone", readonly=True)
    work_email = fields.Char(string="Work Email", readonly=True)
    department_id = fields.Many2one('hr.department', string="Department", readonly=True)
    job_id = fields.Many2one('hr.job', string="Job Position", readonly=True)
    parent_id = fields.Many2one('hr.employee', string="Manager", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True)
    seniority = fields.Char(string="Seniority", readonly=True)
    salary = fields.Float(string='Salary', readonly=True)


    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                (
                    SELECT
                        emp.id,
                        emp.id as employee_id,
                        emp.name,
						emp.work_phone,
						emp.work_email,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id,
                        emp.company_id,
						emp.seniority,
						(hr_contract.wage + hr_contract.non_taxable_allowance + hr_contract.taxable_allowance) as Salary
						
                    FROM (
                        SELECT
                            id,
                            name,
							work_phone,
							work_email,
                            department_id,
                            job_id,
                            parent_id,
                            company_id,
							user_id, 
                            seniority
                        FROM
                            hr_employee
                        ) as emp
                    LEFT JOIN 	
                        hr_contract
                            ON hr_contract.employee_id = emp.id
					WHERE
						hr_contract.state = 'open'
					GROUP BY
						emp.id,
                        emp.name,
						emp.work_phone,
						emp.work_email,
                        emp.department_id,
                        emp.job_id,
                        emp.parent_id,
                        emp.company_id,
						emp.seniority,
						hr_contract.wage,
						hr_contract.non_taxable_allowance,
						hr_contract.taxable_allowance	
                )
            )
        """ % (self._table))

    