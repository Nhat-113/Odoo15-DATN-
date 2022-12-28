
from odoo import models, api,_
from odoo.http import request


class DashboardBlock(models.Model):
    
    _name = "dashboard.block"
    _description = "Dashboard Blocks"


    #get company_id select in menu bar
    def get_current_company_value(self):
            
        cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")] \
            if request.httprequest.cookies.get('cids') \
            else [request.env.user.company_id.id]

        for company_id in cookies_cids:
            if company_id not in self.env.user.company_ids.ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [self.env.company.id]
        if len(cookies_cids) == 1:
            cookies_cids.append(0)
        return cookies_cids

    #get check role user 
    def get_role_user_login(self):
        if self.env.user.has_group('ds_company_management.group_company_management_ceo') == True:
            return 'Ceo'
        elif self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == True and \
				self.env.user.has_group('ds_company_management.group_company_management_ceo') == False:
            return 'Sub-Ceo'
    
    #get data project list
    @api.model
    def get_position_employee(self):
        cr = self._cr

        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value() 
        get_role_user_login = self.get_role_user_login() 
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()
        sql_domain_for_department = ' AND (hr_employee.department_id  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR hr_employee.department_id IS NULL )' 

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department = ''
        else: 
            id_all_mirai_department.append(0)
        sql_domain_for_active = ' AND (hr_employee.active = true )  ' 

        if get_role_user_login  == 'Ceo':
            sql = """SELECT  hr_job.name, count(*)  FROM hr_employee
                        INNER JOIN hr_job on hr_job.id = hr_employee.job_id 
                        LEFT OUTER JOIN hr_department ON hr_employee.department_id = hr_department.id  
                        WHERE hr_employee.company_id IN  """ + str(tuple(selected_companies)) + """
                        """
                        
            sql_group_by =  ' GROUP BY  hr_job.name'
            sql += sql_domain_for_department
            sql += sql_domain_for_active
            sql += sql_group_by

        elif get_role_user_login  == 'Sub-Ceo':
            sql = """SELECT  hr_job.name, count(*)  FROM hr_employee
                        INNER JOIN hr_job on hr_job.id = hr_employee.job_id 
                        LEFT OUTER JOIN hr_department ON hr_employee.department_id = hr_department.id  
                        INNER JOIN RES_COMPANY ON HR_EMPLOYEE.COMPANY_ID = RES_COMPANY.ID
                        INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                        WHERE  hr_employee.company_id IN  """ + str(tuple(selected_companies)) + """
                        """
            sql_domain_for_role = 'AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_group_by =  ' GROUP BY hr_job.name, res_users.id'

            sql += sql_domain_for_department
            sql += sql_domain_for_active
            sql += sql_domain_for_role
            sql += sql_group_by

        cr.execute(sql)

        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})

        return data
    @api.model
    def get_project_status(self):
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value()
        get_role_user_login = self.get_role_user_login() 

        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()
        sql_domain_for_department = ' and (project_project.department_id not in ' + str(tuple(id_all_mirai_department)) + ' or project_project.department_id is null )'

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department = ''
        else: 
            id_all_mirai_department.append(0)
        cr = self._cr
        if get_role_user_login  == 'Ceo':
            sql = """SELECT last_update_status, count(*)  FROM project_project WHERE  company_id IN  """ + str(tuple(selected_companies)) + """ """
            sql_group_by = ' group by last_update_status'
            sql_order_by = ' order by last_update_status '

            sql += sql_domain_for_department
            sql += sql_group_by
            sql += sql_order_by 

        elif get_role_user_login  == 'Sub-Ceo':
            sql = """SELECT project_project.last_update_status, count(*), res_users.id  FROM project_project 
                        INNER JOIN RES_COMPANY ON project_project.COMPANY_ID = RES_COMPANY.ID
                        INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                        WHERE  project_project.company_id IN  """ + str(tuple(selected_companies)) + """ """
            sql_group_by = ' group by last_update_status, res_users.id'
            sql_order_by = ' order by last_update_status '
            sql_domain_for_role = 'AND (res_users.id =  ' + str(user_id_login)  + ')'
            
            sql += sql_domain_for_department
            sql += sql_domain_for_role
            sql += sql_group_by
            sql += sql_order_by 

        cr.execute(sql)
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data

    @api.model
    def get_effort_human_resource(self):
        user_id_login = self.env.user.id
        get_role_user_login = self.get_role_user_login() 

        selected_companies = self.get_current_company_value()
		
        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()		
        # div_manager_department_id =  self.env.user.employee_ids.department_id.id
        cr = self._cr
	
        # sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ' or company_project_id in ' + str(tuple(selected_companies)) + ')'
        sql_domain_for_company = ''

        sql_domain_for_role = ''
        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department_emp = ''
            sql_domain_for_department_proj = ''
        else: 
            id_all_mirai_department.append(0)
            sql_domain_for_department_emp = ' AND (human_resource_management.department_id  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR human_resource_management.department_id IS NULL )'
            sql_domain_for_department_proj = ' AND (human_resource_management.PROJECT_DEPARTMENT_ID  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR human_resource_management.PROJECT_DEPARTMENT_ID IS NULL )' 

        if get_role_user_login  == 'Ceo':
            sql_domain_for_role = ''
            sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ')'


        elif get_role_user_login  == 'Sub-Ceo':
            sql_domain_for_company =   'where ( company_manager_user_id = ' + str(user_id_login) + ' and company_id in ' + str(tuple(selected_companies)) + ')'
            sql_domain_for_role = ''


        sql = ("""select employee_id, project_type_name, month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12,
                        average, department_manager_user_id, company_manager_user_id, start_date_contract,
                        end_date_contract from human_resource_management 
                """)
        sql += sql_domain_for_company
        sql += sql_domain_for_role
        sql += sql_domain_for_department_emp
        sql += sql_domain_for_department_proj

        cr.execute(sql)
        data = cr.fetchall()
        return data    
     
    @api.model
    def get_revenue_company(self):
        selected_companies = self.get_current_company_value()
        get_role_user_login = self.get_role_user_login() 
        user_id_login = self.env.user.id

        cr = self._cr
        if get_role_user_login  == 'Ceo':
            sql  = ("""SELECT to_char(month_start, 'Month YYYY') AS l_month ,SUM(total_revenue)/100000000 AS revenue,
                        SUM(project_management_ceo_data.total_profit)/100000000 AS total_profit, 
                        SUM(total_salary + total_project_cost + total_department_cost + total_avg_operation_company)/100000000  AS cost_data from project_management_ceo_data
                        WHERE   extract(year from month_start)  = extract(year from CURRENT_DATE)   AND  company_id in  """ + str(tuple(selected_companies)) + """
                        group by month_start""")

        elif get_role_user_login  == 'Sub-Ceo':

            sql_domain_for_role = ' AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_order_by   = ' GROUP BY project_management_ceo_data.month_start'  

            sql  = ("""SELECT to_char(project_management_ceo_data.month_start, 'Month YYYY') AS l_month, SUM(project_management_ceo_data.total_revenue)/100000000 AS revenue,
                        SUM(project_management_ceo_data.total_profit)/100000000 AS total_profit, 
                        SUM(project_management_ceo_data.total_salary + project_management_ceo_data.total_project_cost 
                        + project_management_ceo_data.total_department_cost + project_management_ceo_data.total_avg_operation_company)/100000000  AS cost_data 
                        FROM project_management_ceo_data
                        INNER JOIN RES_COMPANY ON project_management_ceo_data.COMPANY_ID = RES_COMPANY.ID
                        INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                        WHERE   extract(year from month_start)  = extract(year from CURRENT_DATE)   AND  project_management_ceo_data.company_id in  """ + str(tuple(selected_companies)) + """
                        """)
            
            sql += sql_domain_for_role
            sql += sql_order_by
        cr.execute(sql)
        data = cr.fetchall()
        
        return data

        
    # get data for contract type
    @api.model
    def get_contract_type(self):
        user_id_login = self.env.user.id
        get_role_user_login = self.get_role_user_login() 
        selected_companies = self.get_current_company_value()

        id_all_mirai_department = self.env['cost.management.upgrade.action'].handle_remove_department()
        sql_domain_for_department = ' and (hr_contract.department_id not in ' + str(tuple(id_all_mirai_department)) + ' or hr_contract.department_id is null )' 

        if len(id_all_mirai_department) == 0: 
            sql_domain_for_department = ''
        else: 
            id_all_mirai_department.append(0)
        sql_order_by =  ' order by hr_contract.contract_document_type '

        cr = self._cr
        if get_role_user_login  == 'Ceo':

            sql = """SELECT hr_contract.contract_document_type ,count(*) FROM hr_contract
                        LEFT OUTER JOIN hr_department ON hr_contract.department_id = hr_department.id 
                        WHERE hr_contract.state = 'open' AND  hr_contract.company_id IN  """ + str(tuple(selected_companies)) + """
                        """
            sql_group_by = ' group by hr_contract.contract_document_type '

            sql += sql_domain_for_department
            sql += sql_group_by
            sql += sql_order_by

        elif get_role_user_login  == 'Sub-Ceo':
            sql = """SELECT hr_contract.contract_document_type ,count(*) FROM hr_contract
                        LEFT OUTER JOIN hr_department ON hr_contract.department_id = hr_department.id 
                        INNER JOIN RES_COMPANY ON hr_contract.COMPANY_ID = RES_COMPANY.ID
                        INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                        WHERE hr_contract.state = 'open' AND  hr_contract.company_id IN  """ + str(tuple(selected_companies)) + """
                    """
            sql_domain_for_role = ' AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_group_by =  ' group by hr_contract.contract_document_type, res_users.id '
            sql += sql_domain_for_department
            sql += sql_domain_for_role
            sql += sql_group_by
            sql += sql_order_by

        cr = self._cr
        cr.execute(sql)
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data
    
    @api.model
    def get_payroll_follow_month(self):
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value() 
        get_role_user_login = self.get_role_user_login() 

        cr = self._cr
        if get_role_user_login  == 'Ceo':
            sql = """SELECT to_char(month_start, 'Month YYYY') AS l_month, sum(total_revenue)/100000000 AS revenue,
                        sum(project_management_ceo_data.total_salary)/100000000  from project_management_ceo_data
                        WHERE   extract(year from month_start)  = extract(year from CURRENT_DATE)   AND  company_id IN  """ + str(tuple(selected_companies)) + """
                        group by month_start """
         
            sql_domain_for_role = ''

        elif get_role_user_login  == 'Sub-Ceo':

            sql_domain_for_role = ' AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_order_by   = ' GROUP BY project_management_ceo_data.month_start'  
            sql  = """ SELECT to_char(month_start, 'Month YYYY') AS l_month, sum(total_revenue)/100000000 AS revenue,
                                sum(project_management_ceo_data.total_salary)/100000000 AS salary  from project_management_ceo_data
                                INNER JOIN RES_COMPANY ON project_management_ceo_data.COMPANY_ID = RES_COMPANY.ID
                                INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                                WHERE   extract(year from month_start)  = extract(year from CURRENT_DATE)   AND  project_management_ceo_data.company_id IN  """ + str(tuple(selected_companies)) + """
                                """
            sql += sql_domain_for_role
            sql += sql_order_by

        cr.execute(sql)
        data = cr.fetchall()
        
        return data
    
    @api.model
    def get_payroll_static_follow_month(self):
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value() 
        get_role_user_login = self.get_role_user_login() 

        cr = self._cr
        if get_role_user_login  == 'Ceo':
            sql = """SELECT EXTRACT(MONTH FROM date_from)   AS l_month,
                        sum(compare_salary_cost_data.total_salary)/100000000  from compare_salary_cost_data
                        WHERE   extract(year from date_from)  = extract(year from CURRENT_DATE)   AND  company_id IN  """ + str(tuple(selected_companies)) + """
                        group by date_from """
         
            sql_domain_for_role = ''

        elif get_role_user_login  == 'Sub-Ceo':

            sql_domain_for_role = ' AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_order_by   = ' GROUP BY compare_salary_cost_data.date_from'  
            sql  = """ SELECT EXTRACT(MONTH FROM date_from) AS l_month,
                                sum(compare_salary_cost_data.total_salary)/100000000 AS salary  from compare_salary_cost_data
                                INNER JOIN RES_COMPANY ON compare_salary_cost_data.COMPANY_ID = RES_COMPANY.ID
                                INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                                WHERE   extract(year from date_from)  = extract(year from CURRENT_DATE)   AND  compare_salary_cost_data.company_id IN  """ + str(tuple(selected_companies)) + """
                                """
            sql += sql_domain_for_role
            sql += sql_order_by

   
        cr.execute(sql)
        
        data_payroll_static = cr.fetchall()
        list_month_data = []
        for item , _ in data_payroll_static:
            list_month_data.append(item)

        
        for index in range(1,13):
            if index not in list_month_data:
                data_payroll_static.append((index,0))

        return {
            'data_payroll_static': data_payroll_static,
            'sql': sql,

        }
    @api.model
    def get_payroll_revenue_follow_month(self):
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value()
        get_role_user_login = self.get_role_user_login() 

        cr = self._cr
        if get_role_user_login  == 'Ceo':
            sql = """SELECT to_char(month_start, 'Month YYYY') AS l_month, sum(project_management_ceo_data.total_revenue)/100000000 AS revenue
                        FROM project_management_ceo_data
                        WHERE   extract(year FROM month_start)  = extract(year FROM CURRENT_DATE)   AND  company_id IN  """ + str(tuple(selected_companies)) + """
                        group by month_start """
         
            sql_domain_for_role = ''

        elif get_role_user_login  == 'Sub-Ceo':

            sql_domain_for_role = ' AND (res_users.id =  ' + str(user_id_login)  + ')'
            sql_order_by   = ' GROUP BY project_management_ceo_data.month_start'  
            sql  = """ SELECT to_char(month_start, 'Month YYYY') AS l_month, sum(project_management_ceo_data.total_revenue)/100000000 AS revenue
                                 FROM project_management_ceo_data
                                INNER JOIN RES_COMPANY ON project_management_ceo_data.COMPANY_ID = RES_COMPANY.ID
                                INNER JOIN res_users ON res_users.login =  RES_COMPANY.USER_EMAIL
                                WHERE   extract(year FROM month_start)  = extract(year FROM CURRENT_DATE)   AND  project_management_ceo_data.company_id IN  """ + str(tuple(selected_companies)) + """
                                """
            sql += sql_domain_for_role
            sql += sql_order_by

        cr.execute(sql)
        data = cr.fetchall()
        
        return data

