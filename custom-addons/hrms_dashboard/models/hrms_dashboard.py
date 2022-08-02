# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
import pandas as pd
from pytz import utc
from soupsieve import select
from datetime import datetime

from odoo import models, fields, api, _
from odoo.http import request
from odoo.tools import float_utils
from datetime import date
import calendar

ROUNDING_FACTOR = 16


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    duration_display = fields.Char('Requested (Days/Hours)', compute='_compute_duration_display', store=True,
                                   help="Field allowing to see the leave request duration"
                                        " in days or hours depending on the leave_type_request_unit")


class Employee(models.Model):
    _inherit = 'hr.employee'

    birthday = fields.Date('Date of Birth', groups="base.group_user", help="Birthday")

    @api.model
    def check_user_group(self):
        uid = request.session.uid
        user = self.env['res.users'].sudo().search([('id', '=', uid)], limit=1)
        if user.has_group('hr.group_hr_manager'):
            return True
        elif user.has_group('hr.group_hr_user'):
            return True
        else:
            return False
    #get company select in menu bar
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
    @api.model
    def get_user_employee_details(self):
        uid = request.session.uid
        company_ids = self.env.user.company_ids.ids
        employee = self.env['hr.employee'].sudo().search_read([('user_id', '=', uid)], limit=1)
        company_id = self.env.company.ids
        leave_manager_id = self.env['hr.employee'].search([('leave_manager_id', '=' ,uid)])
        selected_companies = self.get_current_company_value();

        today = datetime.strftime(datetime.today(), '%Y-%m-%d')
        today_timestamp = datetime.today()
        first_day = datetime.today().replace(day=1)
        last_day = (datetime.today() + relativedelta(months=1, day=1)) - timedelta(1)

        #all request
        if  self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
            # leave to approve 
            leaves_to_approve = self.env['hr.leave'].sudo().search_count([
                ('state', 'in',  ['confirm','draft','refuse', 'validate1']),
                ('employee_company_id','in' , selected_companies )
                ])
            #leave request to day
            leaves_today = self.env['hr.leave'].sudo().search_count([
            ('state', 'in',  ['confirm','draft','refuse', 'validate1']),\
            ('create_date','>=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 0, 0, 0)),\
            ('create_date','<=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 23, 59, 59)),\
            ('employee_company_id','in' , selected_companies )])
            # leave this month
            leaves_this_month = self.env['hr.leave'].sudo().search_count([('state', 'in', ['confirm','refuse', 'validate1']),\
            ('employee_company_id','in' , selected_companies),
            ('create_date','>=',datetime(first_day.year, first_day.month, first_day.day, 0, 0, 0)),\
            ('create_date','<=',datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)),\
            ])
            #all allow request
            leaves_alloc_req = self.env['hr.leave'].sudo().search_count([
            ('state', 'in', ['validate']),
            ('employee_company_id','in' , selected_companies)
            ])
        # time off
        else: 
            #leave to approve
            my_leave_to_app = self.env['hr.leave'].sudo().search_count([
                ('user_id', '=',uid), 
                ('state', 'in',  ['confirm','draft','refuse', 'validate1']),
                ])
            my_staff_leave_to_app =  self.env['hr.leave'].sudo().search_count([
                #('user_id', '=',uid), 
                ('state', 'in',  ['confirm','draft','refuse', 'validate1']),
                ('employee_id', 'in',leave_manager_id.ids)
                ])

            leaves_to_approve = my_leave_to_app +  my_staff_leave_to_app
            #leave today
            my_leave_to_app_today =  self.env['hr.leave'].sudo().search_count([
            ('user_id', '=',uid), 
            ('state', 'in',  ['confirm','draft','refuse', 'validate1']),\
            ('create_date','>=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 0, 0, 0)),\
            ('create_date','<=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 23, 59, 59)),
            ])    
            my_staff_leave_to_app_today = self.env['hr.leave'].sudo().search_count([
            ('employee_id', 'in',leave_manager_id.ids),
            ('state', 'in',  ['confirm','draft','refuse', 'validate1']),\
            ('create_date','>=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 0, 0, 0)),\
            ('create_date','<=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 23, 59, 59)),
            
            ])
            leaves_today =  my_leave_to_app_today +  my_staff_leave_to_app_today
            #leave this month
            my_leave_to_app_this_mon =  self.env['hr.leave'].sudo().search_count([
            ('user_id', '=',uid), 
            ('state', 'in',  ['confirm','draft','refuse', 'validate1']),
            ('create_date','>=',datetime(first_day.year, first_day.month, first_day.day, 0, 0, 0)),
            ('create_date','<=',datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)),
            ])    
            my_staff_leave_to_this_mon = self.env['hr.leave'].sudo().search_count([
            ('employee_id', 'in',leave_manager_id.ids),
            ('state', 'in',  ['confirm','draft','refuse', 'validate1']),
            ('create_date','>=',datetime(first_day.year, first_day.month, first_day.day, 0, 0, 0)),\
            ('create_date','<=',datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59)),
            
            ])
            leaves_this_month = my_leave_to_app_this_mon + my_staff_leave_to_this_mon

            # leave  approved
            my_leaves_alloc_req = self.env['hr.leave'].sudo().search_count([
            ('user_id', '=',uid),
            ('state', 'in', ['validate']),
            #('employee_id', 'in',leave_manager_id.ids)
            ])  
            my_staff__leaves_alloc_req = self.env['hr.leave'].sudo().search_count([
            #('user_id', '=',uid),
            ('state', 'in', ['validate']),
            ('employee_id', 'in',leave_manager_id.ids)])  
            leaves_alloc_req = my_leaves_alloc_req + my_staff__leaves_alloc_req
        
        recruitment = self.env['hr.job'].sudo().search_count([('state', 'in', ['recruit']),('company_id','in' ,selected_companies)])
        today_meeting = self.env['calendar.event'].sudo().search_count([
            ('user_id', '=', uid),
            ('start','>=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 0, 0, 0)),\
            ('start','<=',datetime(today_timestamp.year, today_timestamp.month, today_timestamp.day, 23, 59, 59)),])
        

        # query = """
        # select count(id)
        # from hr_leave
        # where  DATE(hr_leave.create_date) = '%s' and state= 'confirm' """ %  (today)
        # cr = self._cr
        # cr.execute(query)
        # leaves_today = cr.fetchall()
       
        timesheet_count = self.env['account.analytic.line'].sudo().search_count(
            [('project_id', '!=', False), ('user_id', '=', uid)])


        timesheet_view_id = self.env.ref('hr_timesheet.hr_timesheet_line_search')
        
        
        user_id = self.env['res.users'].search([('id', '=', uid)])        
        # query = """
        #         select count(id)
        #         from hr_applicant
        #         WHERE hr_applicant.company_id = '%s' and active = 'true'
        #         """ % (company_id)
        # cr = self._cr
        # cr.execute(query)
        # job_applications_all = cr.fetchall()

        job_applications = self.env['hr.applicant'].sudo().search_count([('active', '!=', False),('company_id','in' , selected_companies )])
        
        if employee:
            sql = """select broad_factor from hr_employee_broad_factor where id =%s"""
            self.env.cr.execute(sql, (employee[0]['id'],))
            result = self.env.cr.dictfetchall()
            broad_factor = result[0]['broad_factor']
            if employee[0]['birthday']:
                diff = relativedelta(datetime.today(), employee[0]['birthday'])
                age = diff.years
            else:
                age = False
            if employee[0]['joining_date']:
                diff = relativedelta(datetime.today(), employee[0]['joining_date'])
                years = diff.years
                months = diff.months
                days = diff.days
                experience = '{} years {} months {} days'.format(years, months, days)
            else:
                experience = False
            if employee:
                data = {
                    'broad_factor': broad_factor if broad_factor else 0,
                    'leaves_to_approve': leaves_to_approve,
                    'leaves_today': leaves_today,
                    'leaves_this_month': leaves_this_month,
                    'leaves_alloc_req': leaves_alloc_req,
                    'emp_timesheets': timesheet_count,
                    'job_applications': job_applications,
                    'timesheet_view_id': timesheet_view_id,
                    'experience': experience,
                    'age': age,
                    'recruitment': recruitment,
                    'today_meeting': today_meeting

                }
                employee[0].update(data)
            return employee
        else:
            return False

    @api.model
    def get_upcoming(self):
        cr = self._cr
        uid = request.session.uid
        employee = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)

        cr.execute("""
          select *,
            (to_char(dob,'ddd')::int-to_char(now(),'ddd')::int+total_days)%total_days as dif
            from (select he.id, he.name, to_char(he.birthday, 'Month dd') as birthday, he.birthday as dob,
            (to_char((to_char(now(),'yyyy')||'-12-31')::date,'ddd')::int) as total_days
            FROM hr_employee he
            ) birth
            where (to_char(dob,'ddd')::int-to_char(now(),'DDD')::int+total_days)%total_days between 0 and 15
            order by dif;""")
        birthday = cr.fetchall()
        # e.is_online # was there below
        #        where e.state ='confirm' on line 118/9 #change
        cr.execute("""select event_event.name , event_event.date_begin  + interval '7' hour ,event_event.date_end  + interval '7' hour  from event_event  
         where event_event.stage_id = '1' or  event_event.stage_id = '2' or  event_event.stage_id = '3' """)
        event = cr.fetchall()
        announcement = []
        user_id = request.session.uid
        sql=("""
                select CURRENT_DATE, project_task.priority_type, project_task.name , project_task.id ,project_task.date_start  , hr_employee.name  from  project_task  
                INNER JOIN  project_task_user_rel on project_task_user_rel.task_id = project_task.id 
                INNER JOIN  hr_employee on hr_employee.user_id = project_task_user_rel.user_id and hr_employee.user_id = %s where DATE(project_task.date_start) = CURRENT_DATE
                            """) %  user_id
        cr.execute(sql)
        # task_for_day = cr.fetchall()

        if employee:
            department = employee.department_id
            job_id = employee.job_id
            sql = """select ha.date_end, ha.date_start,ha.announcement_reason
            from hr_announcement ha
            left join hr_employee_announcements hea
            on hea.announcement = ha.id
            left join hr_department_announcements hda
            on hda.announcement = ha.id
            left join hr_job_position_announcements hpa
            on hpa.announcement = ha.id
            where ha.state = 'approved' and
            ha.date_start <= now()::date and
            ha.date_end >= now()::date and
            (ha.is_announcement = True or
            (ha.is_announcement = False
            and ha.announcement_type = 'employee'
            and hea.employee = %s)""" % employee.id
            if department:
                sql += """ or
                (ha.is_announcement = False and
                ha.announcement_type = 'department'
                and hda.department = %s)""" % department.id
            if job_id:
                sql += """ or
                (ha.is_announcement = False and
                ha.announcement_type = 'job_position'
                and hpa.job_position = %s)""" % job_id.id
            sql += ')'
            cr.execute(sql)
            announcement = cr.fetchall()
        return {
            'birthday': birthday,
            'event': event,
            'announcement': announcement ,
            # 'payslip_batches' :payslip_batches
            # 'task_for_day' : task_for_day
        }
    @api.model
    def get_payroll_for_user(self):
        cr = self._cr
        user_id = request.session.uid
        sql=("""
             select hr_employee.name , hr_payslip.date_from, hr_payslip.date_to , hr_payslip.name,  ROUND(hr_payslip_line.amount)
            from hr_payslip_line
            INNER JOIN hr_payslip
            on hr_payslip.id=hr_payslip_line.slip_id
			INNER JOIN hr_employee 
			on hr_employee.id =  hr_payslip.employee_id
            Where hr_payslip_line.code in ('NET','NET1')  AND  hr_employee.user_id = %s
            """) %  user_id
        # sql=("""
        #         select CURRENT_DATE, project_task.priority_type, project_task.name , project_task.id ,project_task.date_start  , hr_employee.name  from  project_task  
        #         INNER JOIN  project_task_user_rel on project_task_user_rel.task_id = project_task.id 
        #         INNER JOIN  hr_employee on hr_employee.user_id = project_task_user_rel.user_id and hr_employee.user_id = %s 
        #         where DATE(project_task.date_start) = CURRENT_DATE
        #                     """) %  user_id
        cr.execute(sql)
        dat = cr.fetchall()
        data = []
        money = []

        for i in range(0, len(dat)):
            money.append(dat[i][4])
            # money_format = "${:.2f}".format(money)
            data.append({'label': dat[i][1], 'value': sum(money)})
  
        return data
    @api.model
    def get_dept_employee(self):
        cr = self._cr
        cr.execute("""select department_id, hr_department.name,count(*)
        from hr_employee join hr_department on hr_department.id=hr_employee.department_id
        group by hr_employee.department_id,hr_department.name""")
        dat = cr.fetchall()
        data = []
        for i in range(0, len(dat)):
            data.append({'label': dat[i][1], 'value': dat[i][2]})
        return data

    @api.model
    def get_department_leave(self):
        month_list = []
        graph_result = []
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        self.env.cr.execute("""select id, name from hr_department where active=True """)
        departments = self.env.cr.dictfetchall()
        department_list = [x['name'] for x in departments]
        for month in month_list:
            leave = {}
            for dept in departments:
                leave[dept['name']] = 0
            vals = {
                'l_month': month,
                'leave': leave
            }
            graph_result.append(vals)
        sql = """
        SELECT h.id, h.employee_id,h.department_id
             , extract('month' FROM y)::int AS leave_month
             , to_char(y, 'Month YYYY') as month_year
             , GREATEST(y                    , h.date_from) AS date_from
             , LEAST   (y + interval '1 month', h.date_to)   AS date_to
        FROM  (select * from hr_leave where state = 'validate') h
             , generate_series(date_trunc('month', date_from::timestamp)
                             , date_trunc('month', date_to::timestamp)
                             , interval '1 month') y
        where date_trunc('month', GREATEST(y , h.date_from)) >= date_trunc('month', now()) - interval '6 month' and
        date_trunc('month', GREATEST(y , h.date_from)) <= date_trunc('month', now())
        and h.department_id is not null
        """
        self.env.cr.execute(sql)
        results = self.env.cr.dictfetchall()
        leave_lines = []
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'department': line['department_id'],
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month', 'department']).sum()
            result_lines = rf.to_dict('index')
            for month in month_list:
                for line in result_lines:
                    if month.replace(' ', '') == line[0].replace(' ', ''):
                        match = list(filter(lambda d: d['l_month'] in [month], graph_result))[0]['leave']
                        dept_name = self.env['hr.department'].browse(line[1]).name
                        if match:
                            match[dept_name] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] + " " + \
                                result['l_month'].split(' ')[1:2][0]

        return graph_result, department_list

    def get_work_days_dashboard(self, from_datetime, to_datetime, compute_leaves=False, calendar=None, domain=None):
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals_batch(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_total[start.date()] += (stop - start).total_seconds() / 3600
        if compute_leaves:
            intervals = calendar._work_intervals_batch(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals_batch(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals[resource.id]:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return days

    @api.model
    def employee_leave_trend(self):
        leave_lines = []
        month_list = []
        graph_result = []
        for i in range(5, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        uid = request.session.uid
        employee = self.env['hr.employee'].sudo().search_read([('user_id', '=', uid)], limit=1)
        for month in month_list:
            vals = {
                'l_month': month,
                'leave': 0
            }
            graph_result.append(vals)
        sql = """
                SELECT h.id, h.employee_id
                     , extract('month' FROM y)::int AS leave_month
                     , to_char(y, 'Month YYYY') as month_year
                     , GREATEST(y                    , h.date_from) AS date_from
                     , LEAST   (y + interval '1 month', h.date_to)   AS date_to
                FROM  (select * from hr_leave where state = 'validate') h
                     , generate_series(date_trunc('month', date_from::timestamp)
                                     , date_trunc('month', date_to::timestamp)
                                     , interval '1 month') y
                where date_trunc('month', GREATEST(y , h.date_from)) >= date_trunc('month', now()) - interval '6 month' and
                date_trunc('month', GREATEST(y , h.date_from)) <= date_trunc('month', now())
                and h.employee_id = %s
                """
        self.env.cr.execute(sql, (employee[0]['id'],))
        results = self.env.cr.dictfetchall()
        for line in results:
            employee = self.browse(line['employee_id'])
            from_dt = fields.Datetime.from_string(line['date_from'])
            to_dt = fields.Datetime.from_string(line['date_to'])
            days = employee.get_work_days_dashboard(from_dt, to_dt)
            line['days'] = days
            vals = {
                'l_month': line['month_year'],
                'days': days
            }
            leave_lines.append(vals)
        if leave_lines:
            df = pd.DataFrame(leave_lines)
            rf = df.groupby(['l_month']).sum()
            result_lines = rf.to_dict('index')
            for line in result_lines:
                match = list(filter(lambda d: d['l_month'].replace(' ', '') == line.replace(' ', ''), graph_result))
                if match:
                    match[0]['leave'] = result_lines[line]['days']
        for result in graph_result:
            result['l_month'] = result['l_month'].split(' ')[:1][0].strip()[:3] + " " + \
                                result['l_month'].split(' ')[1:2][0]
        return graph_result

    @api.model
    def join_resign_trends(self):
        cr = self._cr
        month_list = []
        join_trend = []
        resign_trend = []
        for i in range(11, -1, -1):
            last_month = datetime.now() - relativedelta(months=i)
            text = format(last_month, '%B %Y')
            month_list.append(text)
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            join_trend.append(vals)
        for month in month_list:
            vals = {
                'l_month': month,
                'count': 0
            }
            resign_trend.append(vals)
        cr.execute('''select to_char(joining_date, 'Month YYYY') as l_month, count(id) from hr_employee
        WHERE joining_date BETWEEN CURRENT_DATE - INTERVAL '12 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month''')
        join_data = cr.fetchall()
        cr.execute('''select to_char(resign_date, 'Month YYYY') as l_month, count(id) from hr_employee
        WHERE resign_date BETWEEN CURRENT_DATE - INTERVAL '12 months'
        AND CURRENT_DATE + interval '1 month - 1 day'
        group by l_month;''')
        resign_data = cr.fetchall()

        for line in join_data:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), join_trend))
            if match:
                match[0]['count'] = line[1]
        for line in resign_data:
            match = list(filter(lambda d: d['l_month'].replace(' ', '') == line[0].replace(' ', ''), resign_trend))
            if match:
                match[0]['count'] = line[1]
        for join in join_trend:
            join['l_month'] = join['l_month'].split(' ')[:1][0].strip()[:3]
        for resign in resign_trend:
            resign['l_month'] = resign['l_month'].split(' ')[:1][0].strip()[:3]
        graph_result = [{
            'name': 'Join',
            'values': join_trend
        }, {
            'name': 'Resign',
            'values': resign_trend
        }]

        return graph_result

    @api.model
    def get_attrition_rate(self):

        month_attrition = []
        monthly_join_resign = self.join_resign_trends()
        month_join = monthly_join_resign[0]['values']
        month_resign = monthly_join_resign[1]['values']
        sql = """
        SELECT (date_trunc('month', CURRENT_DATE))::date - interval '1' month * s.a AS month_start
        FROM generate_series(0,11,1) AS s(a);"""
        self._cr.execute(sql)
        month_start_list = self._cr.fetchall()
        for month_date in month_start_list:
            self._cr.execute("""select count(id), to_char(date '%s', 'Month YYYY') as l_month from hr_employee
            where resign_date> date '%s' or resign_date is null and joining_date < date '%s'
            """ % (month_date[0], month_date[0], month_date[0],))
            month_emp = self._cr.fetchone()
            # month_emp = (month_emp[0], month_emp[1].split(' ')[:1][0].strip()[:3])
            match_join = \
                list(filter(lambda d: d['l_month'] == month_emp[1].split(' ')[:1][0].strip()[:3], month_join))[0][
                    'count']
            match_resign = \
                list(filter(lambda d: d['l_month'] == month_emp[1].split(' ')[:1][0].strip()[:3], month_resign))[0][
                    'count']
            month_avg = (month_emp[0] + match_join - match_resign + month_emp[0]) / 2
            attrition_rate = (match_resign / month_avg) * 100 if month_avg != 0 else 0
            vals = {
                # 'month': month_emp[1].split(' ')[:1][0].strip()[:3] + ' ' + month_emp[1].split(' ')[-1:][0],
                'month': month_emp[1].split(' ')[:1][0].strip()[:3],
                'attrition_rate': round(float(attrition_rate), 2)
            }
            month_attrition.append(vals)


        return month_attrition


class BroadFactor(models.Model):
    _inherit = 'hr.leave.type'

    emp_broad_factor = fields.Boolean(string="Broad Factor", help="If check it will display in broad factor type")
