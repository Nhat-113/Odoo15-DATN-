from odoo import fields, models, tools


class ProjectManagement(models.Model):
    _name = "project.management"
    _description = "Project Management"
    _auto = False
    _rec_name = "project_id"
    
    
    def _compute_last_update_color(self):
        projects = self.env['project.project'].search([])
        for record in self:
            for project in projects:
                if record.project_id.id == project.id:
                    record.last_update_color = project.last_update_color

    def _content_compute_total(self, field, model_relationship, field_related):
        for record in self:
            record[field] = sum(item[field_related] for item in record[model_relationship])

    def _compute_count_member(self):
        self._content_compute_total('count_members', 'project_management_history', 'members')

    def _compute_total_salary_member(self):
        self._content_compute_total('total_salary', 'project_management_history', 'total_salary')

    def _compute_total_project_cost(self):
        self._content_compute_total('project_cost', 'project_expense_management', 'total_expenses')
        
    def _compute_total_profit(self):
        self._content_compute_total('profit', 'project_management_history', 'profit')
            
    def _compute_currency_default(self):
        for record in self:
            record.currency_id = self.env['res.currency'].search([('name', '=', 'VND')])
        

    id = fields.Integer("ID")
    project_id = fields.Many2one('project.project', string="Project")
    director = fields.Many2one('hr.employee', string="Director")
    user_pm = fields.Many2one('res.users', string="Project Manager")
    company_id = fields.Many2one('res.company', string="Company")
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, compute='_compute_currency_default')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    status = fields.Char(string='Status')
    
    # bonus = fields.Float(string="Bonus")
    revenue = fields.Monetary(string="Revenue")
    project_cost = fields.Monetary(string="Project Cost", compute=_compute_total_project_cost)
    profit = fields.Monetary(string="Profit", compute=_compute_total_profit)
    
    total_salary = fields.Monetary(string="Salary Cost", compute=_compute_total_salary_member)
    member_ids = fields.One2many('project.member.management', 'project_management_id', string="Members")
    project_expense_management = fields.One2many('project.expense.management', 'project_management_id', string="Project Cost Management")
    project_management_history = fields.One2many('project.management.history', 'project_management_id', string="Project Management History")
    
    count_members = fields.Float(string='Members', compute=_compute_count_member)
    
    last_update_color = fields.Integer(compute='_compute_last_update_color')
    project_type_id = fields.Many2one("project.type", string="Project Type")
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (  
                WITH project_estimation_merged AS (
                    SELECT
                        ROW_NUMBER() OVER(ORDER BY pr.id ASC) AS id,
                        pr.id AS project_id,
                        pr.user_id AS user_pm,
                        pr.div_manager AS director,
                        pr.company_id,
                        pr.date_start,
                        pr.date AS date_end,
                        pr.last_update_status AS status,
                        est.project_type_id,
                        est.currency_id,

                        (SELECT 
                            SUM(pe.total_expenses) 
                        FROM project_expense_management AS pe 
                        WHERE pe.project_id = pr.id
                        ) AS project_cost,

                        (CASE 
                            WHEN est.stage = (SELECT id 
                                                FROM estimation_status 
                                            WHERE type = 'completed')
                                THEN est.total_cost
                            ELSE 0
                        END
                        ) AS total_cost

                    FROM
                        project_project AS pr 
                    LEFT JOIN estimation_work AS est
                        ON est.id = pr.estimation_id
                    WHERE (EXTRACT(MONTH FROM pr.date_start) < EXTRACT(MONTH FROM CURRENT_DATE)
                        AND EXTRACT(YEAR FROM pr.date_start) = EXTRACT(YEAR FROM CURRENT_DATE))
                        OR EXTRACT(YEAR FROM pr.date_start) < EXTRACT(YEAR FROM CURRENT_DATE)

                    GROUP BY
                        project_id,
                        est.project_type_id,
                        user_pm,
                        director,
                        pr.company_id,
                        pr.date_start,
                        date_end,
                        status,
                        est.stage,
                        est.total_cost,
                        est.currency_id,
                        project_cost
                    )
                    
                    SELECT
                        pem.id,
                        pem.project_id,
                        pem.project_type_id,
                        pem.user_pm,
                        pem.director,
                        pem.company_id,
                        pem.date_start,
                        pem.date_end,
                        pem.status,
                        --- Handling when value is null ---
                        (SELECT COALESCE(NULLIF(pem.project_cost, NULL), 0)) AS project_cost,

                        (CASE 
                        --- Get total cost when estimation exists ---
                            WHEN pem.total_cost <> 0 
                                THEN (CASE 
                                        WHEN pem.currency_id = (SELECT id FROM estimation_currency WHERE name = 'USD')
                                            THEN pem.total_cost * (SELECT usd_convert FROM api_exchange_rate)
                                        WHEN pem.currency_id = (SELECT id FROM estimation_currency WHERE name = 'JPY')
                                            THEN pem.total_cost * (SELECT jpy_convert FROM api_exchange_rate)
                                        ELSE pem.total_cost
                                    END
                                )
                        --- Get project revenue when estimation does not exists ---
                            WHEN prm.revenue_project IS NOT NULL AND prm.revenue_project <> 0
                                THEN (CASE
                                        WHEN prm.currency_id = (SELECT id FROM res_currency WHERE name = 'USD')
                                            THEN prm.revenue_project * (SELECT usd_convert FROM api_exchange_rate)
                                        WHEN prm.currency_id = (SELECT id FROM res_currency WHERE name = 'JPY')
                                            THEN prm.revenue_project * (SELECT jpy_convert FROM api_exchange_rate)
                                        ELSE prm.revenue_project
                                    END
                                )
                            ELSE 0
                        END
                        ) AS revenue

                    FROM project_estimation_merged AS pem
                    LEFT JOIN project_revenue_management AS prm
                        ON pem.project_id = prm.project_id

            ) """ % (self._table)
        )