
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
        cr = self._cr
        cr.execute("""select hr_job.name,count(*) from hr_employee inner join hr_job on hr_job.id = hr_employee.job_id
                        group by  hr_job.name """)

        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})

        return data

    @api.model
    def get_project_status(self):
        cr = self._cr
        cr.execute("""select last_update_status ,count(*)  from project_project 
                        group by last_update_status""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][0], 'value': dat[i][1]})
        return data

    @api.model
    def get_effort_human_resource(self):
        cr = self._cr
        cr.execute("""select employee_name, project_type_name, month1, month2, month3, month4, month5, month6, month7, month8, month9, month10, month11, month12,
                         average, start_date_contract,
                         end_date_contract from human_resource_management""")
        data = cr.fetchall()
        
        return data    
     
    @api.model
    def get_revenue_company(self):
        cr = self._cr
        cr.execute("""select to_char(month_start, 'Month YYYY') as l_month ,sum(total_revenue)/10000000 as revenue, sum(total_members) as members from project_management_ceo
                WHERE   to_char(month_start, 'YYYY') = '2022'
                group by month_start""")
        data = cr.fetchall()
        
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
    
