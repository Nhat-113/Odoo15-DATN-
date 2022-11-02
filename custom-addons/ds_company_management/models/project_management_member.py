from odoo import fields, models, api, tools

class ProjectMemberManagement(models.Model):
    _name = "project.management.member"
    _description = "Project Member Management"
    _auto = False


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH project_planning_department AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY plan.id ASC) AS id,
                        plan.project_id,
                        plan.employee_id,
                        pp.department_id,
                        plan.planning_role_id,
                        plan.start_date,
                        plan.end_date,
                        plan.member_type,
                        plan.effort_rate

                    FROM planning_calendar_resource AS plan 
                    LEFT JOIN project_project AS pp
                        ON pp.id = plan.project_id
                )

                SELECT
                    ppd.id,
                    pm.id AS project_management_id,
                    ppd.project_id,
                    ppd.employee_id,
                    he.company_id,
                    he.job_id,
                    ppd.planning_role_id,
                    he.work_email AS email,
                    he.work_phone AS number_phone,
                    ppd.start_date,
                    ppd.end_date,
                    ppd.member_type,
                    ppd.effort_rate
                FROM project_planning_department AS ppd
                LEFT JOIN project_management AS pm
                        ON ppd.project_id = pm.project_id
                LEFT JOIN hr_employee AS he
                        ON he.id = ppd.employee_id
                        
                WHERE ppd.department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                        
            )""" % (self._table)
        )


    
    
class ProjectMemberManagementData(models.Model):
    _name = "project.management.member.data"
    _description = "Project Member Management Data"
    
    
    
    project_management_id = fields.Many2one('project.management', string="Project Management")

    company_id = fields.Many2one('res.company', string='Company')
    employee_id = fields.Many2one('hr.employee', string="Employee")
    job_id = fields.Many2one('hr.job', string="Job Position")
    planning_role_id = fields.Many2one('planning.roles', string='Roles')
    email = fields.Char(string='Email')
    number_phone = fields.Char(string='Number Phone')
    start_date = fields.Date(string='Start')
    end_date = fields.Date(string='End')
    member_type = fields.Many2one('planning.member.type', string="Member Type")
    effort_rate = fields.Float(string="Effort Rate")
    # salary = fields.Float(string="Salary")
    
    member_details = fields.One2many('project.management.member.detail.data', 'project_members', string="Member detail")
    
    
    
    def view_detail_member(self):
        action = {
            'name': self.employee_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management.member.data',
            'res_id': self.id,
            'view_ids': self.env.ref('ds_company_management.view_form_project_management_member').id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'flags': {'mode': 'readonly'}
        }
        return action