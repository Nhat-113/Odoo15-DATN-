import datetime
from odoo import fields, models


class HumanResourceManagementHistory(models.Model):
    _name = "human.resource.management.history"
    _description = "Human Resource History"

    employee_name = fields.Char('Employee Name', store = True)
    company_name = fields.Char('Company Name', store = True)
    department_name = fields.Char('Department Name', store = True)
    project_name = fields.Char('Project Name', store = True)
    project_type_name = fields.Char('Project Type Name', store = True)
    year_of_project = fields.Char('Year of Project', store = True)

    month1 = fields.Float('Month 1', store = True)
    month2 = fields.Float('Month 2', store = True)
    month3 = fields.Float('Month 3', store = True)
    month4 = fields.Float('Month 4', store = True)
    month5 = fields.Float('Month 5', store = True)
    month6 = fields.Float('Month 6', store = True)
    month7 = fields.Float('Month 7', store = True)
    month8 = fields.Float('Month 8', store = True)
    month9 = fields.Float('Month 9', store = True)
    month10 = fields.Float('Month 10', store = True)
    month11 = fields.Float('Month 11', store = True)
    month12 = fields.Float('Month 12', store = True)
    average = fields.Float("Average", store = True)

    company_manager_user_id = fields.Many2one('res.users', string="Manager Company ID")
    department_manager_user_id = fields.Many2one('res.users', string="Department Manager User")
    company_project_id = fields.Many2one('res.company',string="Company of Project")
    company_id = fields.Integer(string="Company")
    department_id = fields.Many2one('hr.department', string= "Department", store = True)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    project_department_id = fields.Integer(string="Project Department")
    department_manager_project_id = fields.Many2one('res.users', string="Department Manager Project")
    user_id_sub_ceo_project = fields.Integer(string="Sub CEO Project")

    year_history = fields.Integer("Year of History Data")
    start_date_contract = fields.Char("Start Date Contract")
    end_date_contract = fields.Char("End Date Contract")

    def action_generate_new_history(self):
        current_year = datetime.date.today().year + 1
        sql = """
            DELETE FROM human_resource_management_history WHERE year_history=""" + str(current_year) + """;
            INSERT INTO
                human_resource_management_history
                (
                    employee_name,
                    company_name,
                    department_name,
                    project_name,
                    project_type_name,
                    year_of_project,
                    month1,
                    month2,
                    month3,
                    month4,
                    month5,
                    month6,
                    month7,
                    month8,
                    month9,
                    month10,
                    month11,
                    month12,
                    average,
                    company_manager_user_id,
                    department_manager_user_id,
                    company_project_id,
                    company_id,
                    department_id,
                    employee_id,
                    project_department_id,
                    department_manager_project_id,
                    user_id_sub_ceo_project,
                    year_history,
                    start_date_contract,
                    end_date_contract 
                    )
                SELECT
                    employee_name,
                    company_name,
                    department_name,
                    project_name,
                    project_type_name,
                    year_of_project,
                    month1,
                    month2,
                    month3,
                    month4,
                    month5,
                    month6,
                    month7,
                    month8,
                    month9,
                    month10,
                    month11,
                    month12,
                    average,
                    company_manager_user_id,
                    department_manager_user_id,
                    company_project_id,
                    company_id,
                    department_id,
                    employee_id,
                    project_department_id,
                    department_manager_project_id,
                    user_id_sub_ceo_project,
                    """ + str(current_year) + """,
                    start_date_contract,
                    end_date_contract

                FROM human_resource_management;
                
             """
        self.env.cr.execute(sql)