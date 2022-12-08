from odoo import fields, models, tools, _


class ProjectManagementCeo(models.Model):
    _name = 'project.management.ceo'
    _description = 'Project Management CEO'
    _auto = False
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH cost_management_subceo_group AS (
                    SELECT 
                        company_id,
                        month_start,
                        month_end,
                        (SUM(total_members)) AS total_members,
                        (SUM(total_salary)) AS total_salary,
                        (SUM(total_project_cost)) AS total_project_cost,
                        (SUM(total_department_cost)) AS total_department_cost,
                        (SUM(total_avg_operation_department)) AS total_avg_operation_department,
                        (SUM(total_revenue)) AS total_revenue,
                        (SUM(total_commission)) AS total_commission,
                        (SUM(total_profit)) AS total_profit,
                        average_cost_company,
                        currency_id
                        
                    FROM project_management_subceo
                    GROUP BY company_id,
                            month_start,
                            month_end,
                            average_cost_company,
                            currency_id
                ),
                get_available_employee AS (
                    SELECT
                        company_id,
                        months,
                        SUM(available_salary) AS available_salary,
                        SUM(available_mm) AS available_mm
                        
                    FROM available_booking_employee
                    WHERE department_id IS NULL
                    GROUP BY company_id,
                            months
                )

                SELECT
                    --ROW_NUMBER() OVER(ORDER BY cm.month_start ASC) AS id,
                    (cm.company_id*10^7 + 5*10^6 + to_char(month_start, 'YYMMDD')::integer)::bigint AS id,
                    cm.company_id,
                    (CONCAT((EXTRACT(YEAR FROM cm.month_start))::text, ' ', TO_CHAR(cm.month_start, 'Month'))) AS months,
                    cm.month_start,
                    cm.month_end,
                    cm.total_revenue,
                    cm.total_commission,
                    cm.total_members,
                    cm.total_project_cost,
                    cm.total_department_cost,
                    (cm.total_salary + COALESCE(NULLIF(ga.available_salary, NULL), 0)) AS total_salary,
                    (cm.total_profit 
                        - COALESCE(NULLIF(ga.available_salary, NULL), 0)
                        - COALESCE(NULLIF(cm.average_cost_company * ga.available_mm, NULL), 0)
                    ) AS total_profit,
                    (CASE
                        WHEN cm.average_cost_company IS NULL OR ga.available_mm IS NULL
                            THEN COALESCE(NULLIF(cm.total_avg_operation_department, NULL), 0)
                        ELSE cm.average_cost_company * ga.available_mm + COALESCE(NULLIF(cm.total_avg_operation_department, NULL), 0)
                    END) AS total_avg_operation_company,
                    rcu.id AS currency_id
                FROM cost_management_subceo_group AS cm
                LEFT JOIN res_company AS rc
                    ON rc.id = cm.company_id
                LEFT JOIN get_available_employee AS ga
                    ON ga.company_id = cm.company_id
                    AND ga.months = cm.month_start
                LEFT JOIN res_currency AS rcu
                    ON rcu.name = 'VND'
            ) """ % (self._table)
        )
        
    
class ProjectManagementCeoData(models.Model):
    _name = 'project.management.ceo.data'
    _description = 'Project Management CEO Data'
    
    
    company_id = fields.Many2one('res.company', string='Company')
    # representative = fields.Many2one('hr.employee', string='Representative')
    months = fields.Char(string="Month")
    month_start = fields.Date(string="Start")
    month_end = fields.Date(string="End")
    total_members = fields.Float(string='Effort (MM)', digits=(12,3))
    total_salary = fields.Float(string="Salary Cost")
    total_project_cost = fields.Float(string="Prj Expenses")
    total_department_cost = fields.Float(string="Department Expenses")
    total_avg_operation_company = fields.Float(string="Operation Cpn")
    total_revenue = fields.Float(string="Revenue")
    total_commission = fields.Float(string="Commission")
    total_profit = fields.Float(string="Profit")
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(12,2))
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    def get_department_management_detail(self):
        action = {
            'name': self.company_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management.subceo.data',
            'view_ids': self.env.ref('ds_company_management.project_management_subceo_action').id,
            'view_mode': 'tree',
            'domain': [('month_start', '=', self.month_start), ('company_id', '=', self.company_id.id)]
        }
        return action


    def get_available_booking_employees(self):
        datas = self.env['available.booking.employee.data'].search([('company_id', '=', self.company_id.id), 
                                                                    ('department_id', '=', False),
                                                                    ('months', 'in', [self.month_start, self.month_end])])
        view_id = self.env.ref('ds_company_management.view_tree_available_booking_employee').id,
        return {
            'name': _('Available ' + self.company_id.name + ' - ' + self.months),
            'type': 'ir.actions.act_window',
            'res_model': 'available.booking.employee.data',
            'res_ids': datas,
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[view_id, 'list'], [False, 'form']],
            'target': 'new',
            'search_view_id': [self.env.ref('ds_company_management.available_employee_department_search_view').id],
            'context': {'no_breadcrumbs': True},
            'domain': [('company_id', '=', self.company_id.id),
                       ('department_id', '=', False), 
                       ('months', '=', self.month_start)]
        }