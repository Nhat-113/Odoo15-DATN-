from odoo import fields, models, tools


class ProjectManagementCeo(models.Model):
    _name = 'project.management.ceo'
    _description = 'Project Management CEO'
    _auto = False
    
    
    company_id = fields.Many2one('res.company', string='Company')
    representative = fields.Many2one('hr.employee', string='Representative')
    month_start = fields.Date(string="Month Start")
    month_end = fields.Date(string="Month End")
    total_members = fields.Float(string='Members')
    total_salary = fields.Monetary(string="Salary Cost")
    total_project_cost = fields.Monetary(string="Project Cost")
    total_revenue = fields.Monetary(string="Revenue")
    total_profit = fields.Monetary(string="Profit")
    currency_id = fields.Many2one('res.currency', string="Currency")
    
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH hr_payslip_payroll AS (
                    SELECT 
                        hp.employee_id,
                        hp.date_from,
                        hp.date_to,
                        hp.contract_id,
                        hp.state,
                        hpl.total,
                        hpl.code
                    FROM hr_payslip hp
                    LEFT JOIN hr_payslip_line hpl
                                    ON hp.id = hpl.slip_id
                    WHERE hpl.code IN('NET', 'NET1') AND hp.state = 'done'
                ),
                
                cost_management_group AS (
                    SELECT 
                        pms.company_id,
                        he.id AS representative,
                        pms.month_start,
                        pms.month_end,
                        (SUM(pms.total_members)) AS total_members,
                        (SUM(pms.total_salary)) AS total_salary,
                        (SUM(pms.total_project_cost)) AS total_project_cost,
                        (SUM(pms.total_revenue)) AS total_revenue,
                        (SUM(pms.total_profit)) AS total_profit,
                        hpp.total AS salary_manager,
                        pms.currency_id
                        
                    FROM project_management_subceo AS pms
                    LEFT JOIN res_company AS rc
                        ON rc.id = pms.company_id
                    LEFT JOIN hr_employee AS he
                        ON he.work_email = rc.user_email
                    LEFT JOIN hr_payslip_payroll AS hpp
                        ON hpp.employee_id = he.id
                        AND EXTRACT(MONTH FROM pms.month_start) = EXTRACT(MONTH FROM hpp.date_from)
                        AND EXTRACT(YEAR FROM pms.month_start) = EXTRACT(YEAR FROM hpp.date_from)
                    GROUP BY pms.company_id,
                            he.id,
                            pms.month_start,
                            pms.month_end,
                            hpp.total,
                            pms.currency_id
                    )
                        
                    SELECT 
                        ROW_NUMBER() OVER(ORDER BY month_start ASC) AS id,
                        cmg.company_id,
                        cmg.representative,
                        cmg.month_start,
                        cmg.month_end,
                        cmg.total_revenue,
                        cmg.total_project_cost,
                        cmg.currency_id,
                        
                        (CASE
                            WHEN brm.effort_rate_month IS NOT NULL
                                THEN (CASE
                                        WHEN cmg.total_members + (1 - brm.man_month) < 0
                                            THEN 0
                                        ELSE
                                            cmg.total_members + (1 - brm.man_month)
                                    END)
                            ELSE
                                cmg.total_members + 1
                        END) AS total_members,
                        
                        (CASE
                            WHEN cmg.salary_manager IS NULL
                                THEN cmg.total_salary
                            ELSE (CASE
                                    WHEN brm.effort_rate_month IS NULL
                                        THEN cmg.total_salary + cmg.salary_manager
                                    ELSE
                                        cmg.total_salary + cmg.salary_manager - ( cmg.salary_manager * brm.effort_rate_month / 100)
                                END)
                        END) AS total_salary,
                        
                        (CASE
                            WHEN cmg.salary_manager IS NULL
                                THEN cmg.total_profit
                            ELSE (CASE
                                    WHEN brm.effort_rate_month IS NULL
                                        THEN cmg.total_profit - cmg.salary_manager
                                            
                                    --- case when manager join project ---
                                    ELSE cmg.total_profit - (cmg.salary_manager - (cmg.salary_manager * brm.effort_rate_month / 100 ))
                                END)
                        END)::NUMERIC(20, 4) AS total_profit,
                        
                        brm.employee_id,
                        cmg.salary_manager,
                        brm.effort_rate_month

                    FROM cost_management_group AS cmg
                    LEFT JOIN booking_resource_month AS brm
                        ON cmg.representative = brm.employee_id
                        AND EXTRACT(MONTH FROM cmg.month_start) = EXTRACT(MONTH FROM brm.start_date_month)
                        AND EXTRACT(YEAR FROM cmg.month_start) = EXTRACT(YEAR FROM brm.start_date_month)
            ) """ % (self._table)
        )
        
        
    def get_department_management_detail(self):
        action = {
            'name': self.company_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.management.subceo',
            'view_ids': self.env.ref('ds_company_management.project_management_subceo_action').id,
            'view_mode': 'tree',
            'domain': [('month_start', '=', self.month_start), ('company_id', '=', self.company_id.id)]
        }
        return action