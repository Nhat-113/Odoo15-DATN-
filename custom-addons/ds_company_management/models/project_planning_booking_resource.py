from odoo import fields, models, tools, api


class ProjectPlanningBookingResource(models.Model):
    _name = 'project.planning.booking'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    ROW_NUMBER() OVER(ORDER BY start_date_month ASC) AS id,
                    he.company_id AS company_emp,
                    pp.company_id,
                    pl.project_id,
                    pp.department_id,
                    br.employee_id,
                    pl.member_type,
                    pmt.name AS member_type_name,
                    pl.planning_role_id,
                    date_trunc('month', br.start_date_month)::date AS months,
                    br.start_date_month,
                    br.end_date_month,
                    br.man_month,
                    br.effort_rate_month,
                    ((COALESCE(NULLIF(hmp.salary, NULL), 0) + (COALESCE(NULLIF(pc.salary_lbn, NULL), 0))) * (COALESCE(NULLIF(br.effort_rate_month, NULL), 0)) / 100 ) AS salary,
                    pc.salary_lbn,
                    pl.inactive,
                    pl.inactive_date,
                    pl.start_date AS start_booking,
                    pl.end_date AS end_booking,
                    rc.id AS currency_id
                    
                FROM booking_resource_month AS br
                LEFT JOIN planning_calendar_resource AS pl
                    ON br.booking_id = pl.id
                LEFT JOIN planning_member_type AS pmt
                    ON pmt.id = pl.member_type
                LEFT JOIN project_project AS pp
                    ON pl.project_id = pp.id
                    
                LEFT JOIN payslip_get_salary_employee AS hmp
                    ON hmp.employee_id = br.employee_id
                    AND EXTRACT (MONTH FROM br.start_date_month) = EXTRACT (MONTH FROM hmp.date_from)
                    AND EXTRACT (YEAR FROM br.start_date_month) = EXTRACT (YEAR FROM hmp.date_from)
                LEFT JOIN pesudo_contract_generate AS pc
                    ON pc.employee_id = br.employee_id
                    AND EXTRACT(MONTH FROM pc.months) = EXTRACT(MONTH FROM br.start_date_month)
                    AND EXTRACT(YEAR FROM pc.months) = EXTRACT(YEAR FROM br.start_date_month)
                LEFT JOIN res_currency AS rc
                    ON rc.name = 'VND'
                LEFT JOIN hr_employee AS he
		            ON he.id = br.employee_id

                ORDER BY project_id, employee_id, months
            )""" % (self._table)
        )
        

class ProjectPlanningBookingResourceData(models.Model):
    _name = 'project.planning.booking.data'
    _order = 'company_id, project_id, employee_id, months DESC'
    
    
    company_emp = fields.Many2one('res.company', string='Company Employee')
    company_id = fields.Many2one('res.company', string='Company')
    project_id = fields.Many2one('project.project', string='Project')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    currency_id = fields.Many2one('res.currency', string='Currency')
    
    months = fields.Date(string="Month Filter")
    starts = fields.Date(string='Start')
    ends = fields.Date(string='End')
    
    effort_rate = fields.Float(string='Effort Rate (%)')
    man_month = fields.Float(string='Man Month')
    salary = fields.Monetary(string='Salary')
    salary_lbn = fields.Monetary(string='13th Month Salary')
    
    
    
    @api.model
    def upgrade_project_booking_support(self):
        user_update = str(self.env.user.id)
        query = self.query_update_project_planning_booking(user_update)
        self.env.cr.execute(query)
        return
        
    def query_update_project_planning_booking(self, user_update):
        return """
                DELETE FROM project_planning_booking_data;
                INSERT INTO 
                    project_planning_booking_data(
                        company_emp,
                        company_id,
                        project_id,
                        currency_id,
                        employee_id,
                        months,
                        starts,
                        ends,
                        effort_rate,
                        man_month,
                        salary,
                        salary_lbn,
                        create_uid, 
                        write_uid, 
                        create_date, 
                        write_date
                    )  
                SELECT 
                    company_emp,
                    company_id,
                    project_id,
                    currency_id,
                    employee_id,
                    months,
                    start_date_month,
	                end_date_month,
                    effort_rate_month,
                    man_month,
                    salary,
                    salary_lbn,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_planning_booking
                WHERE (member_type_name NOT IN('Shadow Time', 'shadow time') 
                            OR member_type_name IS NULL)
                        AND company_id IN (1, 3);
            """
    

        
class ProjectCountMember(models.Model):
    _name = 'project.count.member.contract'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH compute_total_effort_by_month AS (
                    SELECT 
                        company_id,
                        department_id,
                        project_id,
                        employee_id,
                        months,
                        SUM(man_month) AS man_month,
                        SUM(effort_rate_month) AS effort_rate_month
                 		--SUM(salary) AS salary
                    FROM project_planning_booking
                    WHERE (member_type_name NOT IN('Shadow Time', 'shadow time') 
                            OR member_type_name IS NULL)
                        AND (department_id NOT IN (SELECT department_id FROM department_mirai_fnb)
                            OR department_id IS NULL)
                        AND effort_rate_month > 0
                    GROUP BY company_id,
                        department_id,
                        project_id,
                        employee_id,
                        months
                    ORDER BY department_id, employee_id, months
                ),
                get_contract_employee AS (
                    SELECT 
                        --company_id,
                        --department_id,
                        employee_id,
                        months,
                        SUM(working_day) AS working_day,
                        total_working_day,
                        type_contract
                        
                    FROM pesudo_contract
                    GROUP BY --company_id,
                            --department_id,
                            employee_id,
                            months,
                            total_working_day,
                            type_contract
                )
                SELECT
                    ct.company_id,
                    ct.department_id,
                    ct.project_id,
                    ct.employee_id,
                    ct.months,
                    ct.effort_rate_month,
                    ct.man_month,
                    --ct.salary,
                    gc.working_day,
                    gc.total_working_day,
                    (CASE
                        WHEN gc.working_day IS NULL or gc.total_working_day IS NULL
                            THEN 0
                        ELSE(CASE
                                WHEN gc.working_day <> gc.total_working_day
                                    THEN (gc.working_day / gc.total_working_day) * ct.effort_rate_month / 100
                                ELSE ct.man_month
                            END)
                    END) AS mm,
                    gc.type_contract
                    
                FROM compute_total_effort_by_month AS ct
                LEFT JOIN get_contract_employee AS gc
                    ON gc.employee_id = ct.employee_id
                    AND gc.months = ct.months
            )""" % (self._table)
        )
        
        
class BookingResourceMonthSupport(models.Model):
    _name = 'booking.resource.month.data'
    _order = 'company_id, project_id, employee_id, start_date_month DESC'
    
    booking_id = fields.Many2one('planning.calendar.resource', string='Booking')
    project_id = fields.Many2one('project.project', string='Project')
    company_id = fields.Many2one('res.company', string='Company')
    name = fields.Char(string='Name')
    start_date_month = fields.Date(string='Start Date')
    end_date_month = fields.Date(string='End Date')
    effort_rate_month = fields.Float(string='Effort(%)')
    man_month = fields.Float(string='Man Month')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    
    
    @api.model
    def upgrade_booking_resource_month_support(self):
        user_update = str(self.env.user.id)
        query = self.query_booking_resource_month_support(user_update)
        self.env.cr.execute(query)
        return
        
    def query_booking_resource_month_support(self, user_update):
        return """
                DELETE FROM booking_resource_month_data;
                INSERT INTO 
                    booking_resource_month_data(
                        id,
                        name,
                        start_date_month,
                        end_date_month,
                        effort_rate_month,
                        man_month,
                        booking_id,
                        employee_id,
                        project_id,
                        company_id,
                        create_uid, 
                        write_uid, 
                        create_date, 
                        write_date
                    )  
                SELECT 
                    br.id,
                    br.name,
                    br.start_date_month,
                    br.end_date_month,
                    br.effort_rate_month,
                    br.man_month,
                    br.booking_id,
                    br.employee_id,
                    pl.project_id,
                    pp.company_id,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM booking_resource_month br
                LEFT JOIN planning_calendar_resource pl
                    ON pl.id = br.booking_id
                LEFT JOIN project_project pp
                    ON pp.id = pl.project_id;
            """