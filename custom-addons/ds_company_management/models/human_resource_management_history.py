import datetime
from odoo import fields, models, api
from helper.company_management_common import get_sql_by_department, is_ceo, is_sub_ceo, is_div_manager, is_group_leader


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
        current_year = datetime.date.today().year
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

    # function get data human resource
    @api.model
    def get_list_human_resource_history(self):
        current_user = self.env.user
        selected_companies =  self.env['human.resource.management'].get_current_company_value()
		
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()		
        cr = self._cr
	
        sql_domain_for_company = ''
        sql_for_department = ''
        
        sql_domain_for_department_emp = ''
        sql_domain_for_department_proj = ''

        if len(id_all_mirai_department) > 0: 
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (human_resource_management_history.department_id  NOT IN ' \
                                            + str(tuple(id_all_mirai_department)) \
                                            + ' OR human_resource_management_history.department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (human_resource_management_history.PROJECT_DEPARTMENT_ID  NOT IN ' \
                                            + str(tuple(id_all_mirai_department)) \
                                            + ' OR human_resource_management_history.PROJECT_DEPARTMENT_ID IS NULL )' 

        if is_ceo(current_user):
            sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_sub_ceo(current_user):
            sql_domain_for_company =   'where ( company_manager_user_id = ' + str(current_user.id) \
                                        + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_div_manager(current_user):
            sql_domain_for_company = 'where ('
            sql_for_department = get_sql_by_department(self)
            sql_for_department = sql_for_department.replace('and', '', 1)

        elif is_group_leader(current_user):
            sql_domain_for_company = 'where ('
            sql_for_department = get_sql_by_department(self)
            sql_for_department = sql_for_department.replace('and', '', 1)

        sql = ("""select  	employee_name,
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
                            from human_resource_management_history """)
        sql += sql_domain_for_company
        sql += sql_for_department
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj

        cr.execute(sql)
        list_human_resource_history = cr.fetchall()

        return {
            'list_human_resource_history': list_human_resource_history,
        }


    @api.model
    def get_human_resource_free_history(self):
        current_user = self.env.user
        selected_companies =  self.env['human.resource.management'].get_current_company_value()
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()
        cr = self._cr
        sql_domain_for_company = ''
        sql_for_department = ''
        sql_domain_for_role = ''
        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department_emp = ''
            sql_domain_for_department_proj = ''
        else:
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (human_resource_management_history.department_id  NOT IN ' \
                                            + str(tuple(id_all_mirai_department)) \
                                            + ' OR human_resource_management_history.department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (human_resource_management_history.PROJECT_DEPARTMENT_ID  NOT IN ' \
                                            + str(tuple(id_all_mirai_department)) \
                                            + ' OR human_resource_management_history.PROJECT_DEPARTMENT_ID IS NULL )' 

        sql_domain_for_group_by = 'GROUP BY employee_id, employee_name ,company_name, department_name, company_id, \
                                     year_history, start_date_contract, end_date_contract order by employee_name asc'

        if is_sub_ceo(current_user) and not is_ceo(current_user):
            sql_domain_for_company  = 'where ( company_id in ' + str(tuple(selected_companies))
            sql_domain_for_role = ' and company_manager_user_id = ' + str(current_user.id) + ')'

        elif is_div_manager(current_user) and not is_sub_ceo(current_user):
            sql_domain_for_company = 'where ('
            sql_for_department = get_sql_by_department(self)
            sql_for_department = sql_for_department.replace('and', '', 1)

        elif is_group_leader(current_user) and not is_div_manager(current_user):
            sql_domain_for_company = 'where ('
            sql_for_department = get_sql_by_department(self)
            sql_for_department = sql_for_department.replace('and', '', 1)

        sql = ("""SELECT  employee_id, employee_name, company_name, department_name,
				SUM (month1 ) as month1,
				SUM (month2) as month2,
				SUM (month3) as month3,
				SUM (month4) as month4,
				SUM (month5) as month5,
				SUM (month6) as month6,
				SUM (month7) as month7,
				SUM (month8) as month8,
				SUM (month9) as month9,
				SUM (month10) as month10,
				SUM (month11) as month11,
				SUM (month12) as month12,
				company_id,
				year_history,
				start_date_contract,
				end_date_contract
				FROM human_resource_management_history 
					""")
        sql += sql_domain_for_company
        sql += sql_for_department
        sql += sql_domain_for_role
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj
        sql += sql_domain_for_group_by

        cr.execute(sql)

        get_human_resource_free_history = cr.fetchall()

        return {
            'get_human_resource_free_history': get_human_resource_free_history,
        }

    #get data history support 
    @api.model
    def get_list_human_resource_history_support(self):
        current_user = self.env.user
        selected_companies =  self.env['human.resource.management'].get_current_company_value()
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()		
        # div_manager_department_id =  self.env.user.employee_ids.department_id.id
        cr = self._cr
	
        # sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ' or company_project_id in ' + str(tuple(selected_companies)) + ')'
        sql_domain_for_company = ''
        sql_domain_for_role = ''
        sql_domain_for_department_emp = ''
        sql_domain_for_department_proj = ''
        if len(id_all_mirai_department) != 0: 
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (human_resource_management_history.department_id  NOT IN ' \
                + str(tuple(id_all_mirai_department)) + ' OR human_resource_management_history.department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (human_resource_management_history.PROJECT_DEPARTMENT_ID  NOT IN ' \
                + str(tuple(id_all_mirai_department)) + ' OR human_resource_management_history.PROJECT_DEPARTMENT_ID IS NULL )' 
        
        if is_ceo(current_user):
            sql_domain_for_company = ' where company_id != company_project_id and \
                                    ( company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_sub_ceo(current_user):
            sql_domain_for_company = ' where ( company_manager_user_id != ' + str(current_user.id) \
                                    + ' and user_id_sub_ceo_project = ' + str(current_user.id) \
                                    + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        elif is_div_manager(current_user) or is_group_leader(current_user):
            sql_domain_for_role = ' where ( (department_manager_user_id != ' + str(current_user.id) \
                                + ' or department_manager_user_id is null  )' \
                                + ' and department_manager_project_id = ' + str(current_user.id) \
                                + ' and company_id in ' + str(tuple(selected_companies)) + ')'

        sql = ("""select  	employee_name,
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
                            from human_resource_management_history """)
        sql += sql_domain_for_company
        sql += sql_domain_for_role
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj

        cr.execute(sql)
        list_human_resource_history_support = cr.fetchall()

        return {
            'list_human_resource_history_support': list_human_resource_history_support,
        }