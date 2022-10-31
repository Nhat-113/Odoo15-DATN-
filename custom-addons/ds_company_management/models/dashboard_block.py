
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
        cr = self._cr
        cr.execute("""select hr_job.name,count(*) from hr_employee inner join hr_job on hr_job.id = hr_employee.job_id
                       where  hr_employee.company_id in  """ + str(tuple(selected_companies)) + """
                       group by  hr_job.name """)

        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})

        return data

    @api.model
    def get_project_status(self):
        selected_companies = self.get_current_company_value(); 
        cr = self._cr
        cr.execute("""select last_update_status ,count(*)  from project_project 
                        where  company_id in  """ + str(tuple(selected_companies)) + """
                        group by last_update_status""")
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
        
        sql_domain_for_company = 'where ( company_id in ' + str(tuple(selected_companies)) + ' or company_project_id in ' + str(tuple(selected_companies)) + ')'
        sql_domain_for_role = ''
        sql_order_by = '  order by employee_id'
         

        if self.env.user.has_group('ds_company_management.group_company_management_ceo') == True:
            sql_domain_for_role = ''

        elif self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_ceo') == False:
            sql_domain_for_role = ' or company_manager_user_id = ' + str(user_id_login)

        elif self.env.user.has_group('ds_company_management.group_company_management_div') == True and \
                self.env.user.has_group('ds_company_management.group_company_management_sub_ceo') == False:
            sql_domain_for_role = ' and (department_manager_user_id = ' + str(user_id_login) + ' or department_manager_project_id = ' + str(user_id_login) + ')'

        sql = ("""select employee_id, project_type_name, month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12,
                        average, department_manager_user_id, company_manager_user_id, start_date_contract,
                        end_date_contract from human_resource_management 
                """)
        sql += sql_domain_for_company
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

    #get data department type
    @api.model
    def get_dept_employee(self):
        selected_companies = self.get_current_company_value(); 
        cr = self._cr
        cr.execute("""select department_id, hr_department.name,count(*)
                        from hr_employee join hr_department on hr_department.id=hr_employee.department_id
                        WHERE  company_id in  """ + str(tuple(selected_companies)) + """
                        group by hr_employee.department_id,hr_department.name
                    """)
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data
        
    # get data for contract type
    @api.model
    def get_contract_type(self):
        selected_companies = self.get_current_company_value(); 
        cr = self._cr
        cr.execute("""select hr_contract.contract_document_type ,count(*) from hr_contract
                        where hr_contract.state = 'open' and  company_id in  """ + str(tuple(selected_companies)) + """
                        group by hr_contract.contract_document_type""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data
    
    #get data payroll follow months 
    @api.model
    def get_payroll_follow_month(self):
        company_id = self.get_current_company_value()
        cr = self._cr
        cr.execute("""SELECT hr_payslip.date_from, hr_payslip.date_to ,
                        hr_payslip.name, hr_payslip_line.slip_id, hr_payslip.id, (hr_payslip_line.amount)/1000000
                        FROM hr_payslip_line
                        INNER JOIN hr_payslip
                        ON hr_payslip.id=hr_payslip_line.slip_id
                        Where hr_payslip.company_id IN  """ + str(tuple(company_id)) + """ and ( hr_payslip_line.code = 'NET' or  hr_payslip_line.code = 'NET1' or  hr_payslip_line.code = 'HOUR' )
                        and  EXTRACT(YEAR FROM hr_payslip.date_from)  = EXTRACT(YEAR FROM NOW())
                        and hr_payslip.state = 'done' 
                        order by  hr_payslip.date_from 
                    """)
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
    
