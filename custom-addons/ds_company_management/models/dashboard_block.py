
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


    
    #get data project list
    @api.model
    def get_position_employee(self):
        selected_companies = self.get_current_company_value(); 
        id_all_mirai_department = self.env['project.management'].handle_remove_department()

        cr = self._cr
        sql = """SELECT  hr_job.name, count(*)  FROM hr_employee
                    INNER JOIN hr_job on hr_job.id = hr_employee.job_id 
                    LEFT OUTER JOIN hr_department ON hr_employee.department_id = hr_department.id  
                    WHERE  hr_employee.company_id IN  """ + str(tuple(selected_companies)) + """
                       """

        sql_domain_for_department = ' AND (hr_employee.department_id  NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR hr_employee.department_id IS NULL )' 
        sql_group_by =  ' GROUP BY  hr_job.name'

        sql += sql_domain_for_department
        sql += sql_group_by

        cr.execute(sql)

        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})

        return data
    @api.model
    def get_project_status(self):
        selected_companies = self.get_current_company_value(); 
        id_all_mirai_department = self.env['project.management'].handle_remove_department()

        cr = self._cr
        sql = """SELECT last_update_status, count(*)  FROM project_project WHERE  company_id IN  """ + str(tuple(selected_companies)) + """ """
        sql_domain_for_department = ' and (project_project.department_id not in ' + str(tuple(id_all_mirai_department)) + ' or project_project.department_id is null )' 

        sql_group_by = ' group by last_update_status'

        sql += sql_domain_for_department
        sql += sql_group_by

        cr.execute(sql)
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data

    @api.model
    def get_effort_human_resource(self):
        user_id_login = self.env.user.id
        selected_companies = self.get_current_company_value();

        cr = self._cr
        
        sql_domain_for_company = 'WHERE ( company_id IN ' + str(tuple(selected_companies)) + ' OR company_project_id in ' + str(tuple(selected_companies)) + ')'
        id_all_mirai_department = self.env['project.management'].handle_remove_department()

        sql_domain_for_department = ' AND (human_resource_management.department_id NOT IN ' + str(tuple(id_all_mirai_department)) + ' OR human_resource_management.department_id IS NULL )' 
        # sql_domain_for_project_department = ' and (human_resource_management.department_id not in ' + str(tuple(id_all_mirai_department)) + ' or human_resource_management.department_id is null )' 

        sql_domain_for_role = ''
        sql_order_by = '  ORDER BY employee_id'
         

        if self.env.user.has_group('ds_company_management.group_company_management_ceo') == True:
            sql_domain_for_role = ''

        elif self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_ceo') == False:
            sql_domain_for_role = ' OR company_manager_user_id = ' + str(user_id_login)

        elif self.env.user.has_group('ds_company_management.group_company_management_div') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == False:
            sql_domain_for_role = ' AND (department_manager_user_id = ' + str(user_id_login) + ' OR department_manager_project_id = ' + str(user_id_login) + ')'

        sql = ("""select employee_id, project_type_name, month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12,
                        average, department_manager_user_id, company_manager_user_id, start_date_contract,
                        end_date_contract from human_resource_management 
                """)
        sql += sql_domain_for_company
        sql += sql_domain_for_department
        sql += sql_domain_for_role
        sql += sql_order_by

        cr.execute(sql)
        data = cr.fetchall()
        return data    
     
    @api.model
    def get_revenue_company(self):
        selected_companies = self.get_current_company_value(); 
        cr = self._cr
        cr.execute("""select to_char(month_start, 'Month YYYY') as l_month ,sum(total_revenue)/100000000 as revenue,
                        sum(total_members) as members from project_management_ceo_data
                         WHERE   extract(year from month_start)  = extract(year from CURRENT_DATE)   and  company_id in  """ + str(tuple(selected_companies)) + """
                        group by month_start""")
        data = cr.fetchall()
        
        return data

        
    # get data for contract type
    @api.model
    def get_contract_type(self):

        id_all_mirai_department = self.env['project.management'].handle_remove_department()
        selected_companies = self.get_current_company_value(); 
        
        cr = self._cr
        sql = """SELECT hr_contract.contract_document_type ,count(*) FROM hr_contract
                    LEFT OUTER JOIN hr_department ON hr_contract.department_id = hr_department.id 
                    WHERE hr_contract.state = 'open' AND  hr_contract.company_id IN  """ + str(tuple(selected_companies)) + """
                    """
        sql_domain_for_department = ' and (hr_contract.department_id not in ' + str(tuple(id_all_mirai_department)) + ' or hr_contract.department_id is null )' 

        sql_order_by =  ' group by hr_contract.contract_document_type '
        
        sql += sql_domain_for_department
        sql += sql_order_by

        cr = self._cr
        cr.execute(sql)
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data
    
    #get data payroll follow months 
    @api.model
    def get_payroll_follow_month(self):
        # SELECT hr_payslip.date_from, hr_payslip.date_to,
        #                 hr_payslip.name, hr_payslip_line.slip_id, hr_payslip.id, (hr_payslip_line.amount)/1000000,
		# 				hr_payslip.employee_id,hr_employee.department_id,
		# 				hr_department.parent_id
        #                 FROM hr_payslip_line
        #                 INNER JOIN hr_payslip					
        #                 ON hr_payslip.id=hr_payslip_line.slip_id
        #                 INNER JOIN hr_employee
        #                 ON hr_employee.id = hr_payslip.employee_id
		# 				LEFT OUTER JOIN hr_department ON hr_employee.department_id = hr_department.id 
        #                 Where ( hr_payslip_line.code = 'NET' or  hr_payslip_line.code = 'NET1' or  hr_payslip_line.code = 'HOUR' )
        #                 and  EXTRACT(YEAR FROM hr_payslip.date_from)  = EXTRACT(YEAR FROM NOW())
        #                 and hr_payslip.state = 'done' 
		# 				and  (hr_employee.department_id != 27 or hr_employee.department_id is null)  
		# 				and (hr_department.parent_id != 27 or hr_department.parent_id is null)
        #                 order by  hr_payslip.date_from 
        
        company_id = self.get_current_company_value()
        id_all_mirai_department = self.env['project.management'].handle_remove_department()

        sql_domain_for_department = ' AND ( hr_employee.department_id NOT IN ' + str(tuple(id_all_mirai_department)) +  ' OR hr_employee.department_id is null )' 
        sql_order_by =  ' ORDER BY  hr_payslip.date_from '
        
        cr = self._cr
        sql = """SELECT hr_payslip.date_from, hr_payslip.date_to,
                        hr_payslip.name, hr_payslip_line.slip_id, hr_payslip.id, (hr_payslip_line.amount)/1000000
                        FROM hr_payslip_line
                        INNER JOIN hr_payslip					
                        ON hr_payslip.id=hr_payslip_line.slip_id
                        INNER JOIN hr_employee
                        ON hr_employee.id = hr_payslip.employee_id
						LEFT OUTER JOIN hr_department ON hr_employee.department_id = hr_department.id 
                        Where  EXTRACT(YEAR FROM hr_payslip.date_from)  = EXTRACT(YEAR FROM NOW())
                        AND ( hr_payslip_line.code = 'NET' OR  hr_payslip_line.code = 'NET1' OR  hr_payslip_line.code = 'HOUR' )
                        AND ( hr_payslip_line.code = 'NET' OR  hr_payslip_line.code = 'NET1' OR  hr_payslip_line.code = 'HOUR' )
                        AND hr_payslip.state = 'done' 
                        AND hr_payslip.company_id IN  """ + str(tuple(company_id)) + """ """
                       
        sql += sql_domain_for_department  
        sql += sql_order_by
        
        cr.execute(sql)
        dat = cr.fetchall()
        data_payroll = []
        # sum = 0 
        for i in range(0, len(dat)):
            data_payroll.append({'label': dat[i][0], 'value': dat[i][5] })

        data = []
        years = []
        months = []
        for item in data_payroll:
            if item['label'].year not in years:
                years.append(item['label'].year)
            if item['label'].month not in months:
                months.append(item['label'].month)

        for year in years:
            for month in months:
                sum = 0
                for item in data_payroll:
                    if (item['label'].month==month)and(item['label'].year==year):
                        sum += item['value']
                if sum:
                    data.append({'label':[month, year], 'value': sum})
            
        return data
    
    # @api.model
    # def join_resign_trends(self):
    #     cr = self._cr
    #     month_list = []
    #     join_trend = []
    #     resign_trend = []
    #     for i in range(11, -1, -1):
    #         last_month = datetime.now() - relativedelta(months=i)
    #         text = format(last_month, '%B %Y')
    #         month_list.append(text)
    #     for month in month_list:
    #         vals = {
    #             'l_month': month,
    #             'count': 0
    #         }
            
    #         join_trend.append(vals)
    #     for month in month_list:
    #         vals = {
    #             'l_month': month,
    #             'count': 0
    #         }
    #         resign_trend.append(vals)
            
    #     cr.execute('''select to_char(month_start, 'Month YYYY') as l_month ,sum(total_revenue)/10000000 as revenue from project_management_ceo
	#         	WHERE   to_char(month_start, 'YYYY') = '2022'
    #                 group by month_start''')
    #     join_data = cr.fetchall()
        
    #     cr.execute('''		
    #         select to_char(month_start, 'Month YYYY') as l_month , sum(total_members) as members from project_management_ceo
    #             WHERE   to_char(month_start, 'YYYY') = '2022'
    #             group by month_start''')
    #     resign_data = cr.fetchall()

    #     for line in join_data:
    #         match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), join_trend))
    #         if match:
    #             match[0]['count'] = line[1]
    #     for line in resign_data:
    #         match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), resign_trend))
    #         if match:
    #             match[0]['count'] = line[1]
    #     for join in join_trend:
    #         join['l_month'] = join['l_month'].split(' ')[:1][0].strip()[:3]
    #     for resign in resign_trend:
    #         resign['l_month'] = resign['l_month'].split(' ')[:1][0].strip()[:3]
    #     graph_result = [{
    #         'name': 'Join',
    #         'values': join_trend
    #     }, {
    #         'name': 'Resign',
    #         'values': resign_trend
    #     }]

    #     return graph_result
    
