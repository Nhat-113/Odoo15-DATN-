from odoo import fields, models, tools, _


class ProjectManagementSubCeo(models.Model):
    _name = 'project.management.subceo'
    _description = 'Project Management Sub CEO'
    _auto = False
    _order = "id desc"
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH project_history_department AS (
                    SELECT
                        pm.company_id,
                        pm.department_id,
                        -- get first day of month ---
                        (date_trunc('month', pmh.month_start))::date AS month_start,
                        pmh.members,
                        pmh.total_project_expense AS project_cost,
                        pmh.total_department_expense AS department_cost,
                        pmh.profit,
                        pmh.total_salary AS salary_cost,
                        pmh.revenue,
                        pmh.total_commission,
                        pmh.total_avg_operation_project,
                        pmh.average_cost_company,
                        pmh.currency_id

                    FROM project_management AS pm
                    RIGHT JOIN project_management_history AS pmh
                            ON pm.id = pmh.project_management_id
                ),

                --- Group by company, department, month of project history management ---
                project_history_department_group AS (
                    SELECT
                        company_id,
                        department_id,
                        month_start,
                        SUM (members) AS members,
                        SUM (project_cost) AS project_cost,
                        SUM (department_cost) AS department_cost,
                        SUM (revenue) AS revenue,
                        SUM (total_commission) AS total_commission,
                        SUM (salary_cost) AS salary_cost,
                        SUM (profit) AS profit,
                        SUM (total_avg_operation_project) AS total_avg_operation_project,
                        -- average_cost_company,
                        currency_id
                            
                    FROM project_history_department
                    GROUP BY
                            company_id,
                            department_id,
                            month_start,
                            -- average_cost_company,
                            currency_id
                ),
                compute_average_cost_company_for_any_department AS (
                    SELECT
                        company_id,
                        month_start,
                        average_cost_company

                    FROM project_history_department
                    GROUP BY company_id,
                            month_start,
                            average_cost_company
                ),

                --- compute max duration for generate month for department by revenue management of company expense
                compute_max_duration_department AS (
                    SELECT
                        (CASE
                            WHEN max(sort_date) < CURRENT_DATE::DATE
                                THEN (date_trunc('month',CURRENT_DATE))::DATE
                            ELSE max(sort_date)
                        END) AS max_months,
                        pp.department_id
                    FROM project_revenue_value AS prv
                    LEFT JOIN project_project AS pp
                        ON pp.id = prv.project_id
                    GROUP BY pp.department_id
                ),

                department_by_month AS (
                    SELECT
                        generate_series(
                                date_trunc('month', '1/1/2021'::date), 
                                date_trunc('month', 
                                    (CASE
                                        WHEN cm.max_months IS NULL
                                            THEN (date_trunc('month',CURRENT_DATE))::DATE
                                        ELSE cm.max_months
                                    END)
                                ),
                                '1 month'
                        )::date AS months,
                        hd.id AS department_id,
                        hd.manager_id,
                        hd.company_id
                        
                        FROM hr_department AS hd
                        LEFT JOIN compute_max_duration_department AS cm
                            ON cm.department_id = hd.id
                        WHERE hd.id NOT IN (SELECT department_id FROM department_mirai_fnb)
                ),
                get_available_employee AS (
                    SELECT
                        department_id,
                        months,
                        SUM(available_salary) AS available_salary,
                        SUM(available_mm) AS available_mm
                        
                    FROM available_booking_employee
                    WHERE department_id IS NOT NULL
                    GROUP BY department_id,
                            months
                )
                    
                SELECT
                    ROW_NUMBER() OVER(ORDER BY dbm.months ASC) AS id,
                    dbm.company_id,
                    dbm.department_id,
                    (CONCAT((EXTRACT(YEAR FROM dbm.months))::text, ' ', TO_CHAR(dbm.months, 'Month'))) AS months,
                    dbm.months AS month_start,
                    (date_trunc('month', dbm.months) + interval '1 month - 1 day'
                    )::date AS month_end,

                    -- remaining_member & remaining_salary manager have been calculated
                    COALESCE(NULLIF(phdg.members,		NULL), 0) AS total_members,
                    COALESCE(NULLIF(phdg.project_cost,	NULL), 0)  AS total_project_cost,
                    COALESCE(NULLIF(phdg.department_cost,	NULL), 0)  AS total_department_cost,
                    COALESCE(NULLIF(phdg.revenue, 		NULL), 0)  AS total_revenue,
                    COALESCE(NULLIF(phdg.total_commission, NULL), 0)  AS total_commission,
                    COALESCE(NULLIF(phdg.salary_cost, 	NULL), 0) + COALESCE(NULLIF(ga.available_salary, NULL), 0) AS total_salary,
                    (COALESCE(NULLIF(phdg.profit, 		NULL), 0) 
                        - COALESCE(NULLIF(ga.available_salary, NULL), 0) 
                        - COALESCE(NULLIF(cac.average_cost_company * ga.available_mm, NULL), 0) 
                    ) AS total_profit,
                    COALESCE(NULLIF(ga.available_salary, NULL), 0) AS available_salary,
                    COALESCE(NULLIF(cac.average_cost_company, NULL), 0) AS average_cost_company,
                    (CASE
                        WHEN cac.average_cost_company IS NULL OR ga.available_mm IS NULL
                            THEN COALESCE(NULLIF(phdg.total_avg_operation_project, NULL), 0)
                        ELSE cac.average_cost_company * ga.available_mm + COALESCE(NULLIF(phdg.total_avg_operation_project, NULL), 0)
                    END) AS total_avg_operation_department,
                    
                    rcr.id AS currency_id,
                    ru.id AS user_login
                    
                FROM department_by_month AS dbm
                LEFT JOIN project_history_department_group AS phdg
                    ON phdg.company_id = dbm.company_id
                    AND phdg.department_id = dbm.department_id
                    AND phdg.month_start = dbm.months
                LEFT JOIN get_available_employee AS ga
                    ON ga.department_id = dbm.department_id
                    AND ga.months = dbm.months
                LEFT JOIN compute_average_cost_company_for_any_department AS cac
                    ON cac.company_id = dbm.company_id
                    AND cac.month_start = dbm.months
                LEFT JOIN res_company AS rc
                    ON rc.id = dbm.company_id
                LEFT JOIN res_users AS ru
                    ON ru.login = rc.user_email
                LEFT JOIN res_currency AS rcr
                    ON rcr.name = 'VND'
                ORDER BY company_id, department_id, month_start

            ) """ % (self._table)
        )
        
        
class ProjectManagementSubCeoData(models.Model):
    _name = 'project.management.subceo.data'
    _description = 'Project Management Sub CEO Data'
    _order = "id desc"
     
    
    company_id = fields.Many2one('res.company', string='Company')
    department_id = fields.Many2one('hr.department', string='Department')
    months = fields.Char(string="Month")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    total_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_project_cost = fields.Float(string="Prj Expenses")
    total_department_cost = fields.Float(string="Department Expenses")
    total_avg_operation_department = fields.Float(string="Total OP Avg Prj")
    total_revenue = fields.Float(string="Revenue")
    total_commission = fields.Float(string="Commission")
    total_profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2))
    
    currency_id = fields.Many2one('res.currency', string="Currency")
    user_login = fields.Many2one('res.users', string="User")
    
         
    def get_project_detail(self):
        action = {
            'name': self.department_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'department.project.detail.data',
            'view_ids': self.env.ref('ds_company_management.department_project_detail_action').id,
            'view_mode': 'tree',
            'domain': [('department_id', '=', self.department_id.id), 
                       ('company_id', '=', self.company_id.id),
                       ('months_domain', 'in', [self.month_start, self.month_end])]
        }
        return action
    
    
    def get_available_booking_employees(self):
        datas = self.env['available.booking.employee.data'].search([('company_id', '=', self.company_id.id), 
                                                                    ('department_id', '=', self.department_id.id),
                                                                    ('months', 'in', [self.month_start, self.month_end])])
        view_id = self.env.ref('ds_company_management.view_tree_available_booking_employee').id,
        return {
            'name': _('Available ' + self.department_id.name + ' - ' + self.months),
            'type': 'ir.actions.act_window',
            'res_model': 'available.booking.employee.data',
            'res_ids': datas,
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[view_id, 'list'], [False, 'form']],
            'target': 'new',
            'search_view_id': [self.env.ref('ds_company_management.available_employee_department_search_view').id],
            'context': {'no_breadcrumbs': True},
            'domain': [('department_id', '=', self.department_id.id), 
                       ('company_id', '=', self.company_id.id),
                       ('months', 'in', [self.month_start, self.month_end])]
        }