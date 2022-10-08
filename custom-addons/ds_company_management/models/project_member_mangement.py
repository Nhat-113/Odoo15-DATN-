from odoo import fields, models, api, tools

class ProjectMemberManagement(models.Model):
    _name = "project.member.management"
    _description = "Project Member Management"
    _auto = False

    
    project_management_id = fields.Many2one('project.management', string="Project Management")

    employee_id = fields.Many2one('hr.employee', string="Employee")
    job_id = fields.Many2one('hr.job', string="Job Position")
    role_ids = fields.Many2one('config.job.position', string='Roles')
    email = fields.Char(string='Email')
    number_phone = fields.Char(string='Number Phone')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    member_type = fields.Many2one('planning.member.type', string="Member Type")
    effort_rate = fields.Float(string="Effort Rate")
    # salary = fields.Float(string="Salary")
    
    def init(self):
        # project_managements = self.env['project.management'].search([])
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                SELECT
                    ROW_NUMBER() OVER(ORDER BY employee_id ASC) AS id,
                    pm.id AS project_management_id,
                    plan.project_id,
                    plan.employee_id,
                    he.job_id,
                    plan.role_ids,
                    he.work_email AS email,
                    he.work_phone AS number_phone,
                    plan.start_date,
                    plan.end_date,
                    plan.member_type,
                    plan.effort_rate

                FROM planning_calendar_resource AS plan 
                LEFT JOIN project_management AS pm
                    ON plan.project_id = pm.project_id
                LEFT JOIN hr_employee AS he
                    ON he.id = plan.employee_id
                        
            )""" % (self._table)
        )
