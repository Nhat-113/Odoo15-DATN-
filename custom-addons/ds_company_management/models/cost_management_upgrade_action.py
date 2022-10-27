from odoo import models, api


class UpgradeAction(models.Model):
    _name = 'cost.management.upgrade.action'
    
    
    @api.model
    def cost_management_reset_update_data(self):
        user_update = str(self.env.user.id)
        all_query = self.query_project_management(user_update) +\
                    self.query_project_management_history(user_update) +\
                    self.query_project_management_member(user_update) +\
                    self.query_project_management_member_detail(user_update) +\
                    self.query_department_project_detail(user_update) +\
                    self.query_project_management_ceo(user_update) +\
                    self.query_project_management_subceo(user_update)

        self.env.cr.execute(all_query)
        
        # get default project_management_id for project cost management [Company expense]
        project_expenses = self.env['project.expense.value'].sudo().search([])
        for record in project_expenses:
            record.project_management_id = self.env['project.management.data'].search([('project_id', '=', record.project_id.id)]).id
        return
        # return {'type': 'ir.actions.client', 'tag': 'reload'}
    

    def query_project_management(self, user_update):
        return """
                DELETE FROM project_management_data;
                INSERT INTO 
                    project_management_data(
                        id, 
                        project_id, 
                        department_id, 
                        company_id, 
                        project_type_id, 
                        currency_id, 
                        user_pm, 
                        user_login, 
                        sub_user_login, 
                        date_start, 
                        date_end, 
                        status, 
                        count_members, 
                        total_salary, 
                        profit, 
                        project_cost, 
                        revenue, 
                        profit_margin,
                        create_uid, 
                        write_uid, 
                        create_date, 
                        write_date
                    )  
                SELECT 
                    pm.id,
                    pm.project_id,
                    pm.department_id,
                    pm.company_id,
                    pm.project_type_id,
                    pm.currency_id,
                    pm.user_pm,
                    pm.user_login,
                    pm.sub_user_login,
                    pm.date_start,
                    pm.date_end,
                    pm.status,
                    phg.total_members AS count_members,
                    phg.total_salary AS total_salary,
                    phg.total_profit AS profit,
                    pm.project_cost,
                    pm.revenue,
                    (CASE
                        WHEN pm.revenue = 0
                            THEN 0
                        ELSE (phg.total_profit / pm.revenue) * 100
                    END) AS profit_margin,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE

                FROM project_management AS pm
                LEFT JOIN project_history_group_temp AS phg
                    ON phg.project_management_id = pm.id;
       
            """
           
             
    def query_project_management_history(self, user_update):
        return """
                DELETE FROM project_management_history_data;
                INSERT INTO
                    project_management_history_data(
                        id,
                        project_management_id,
                        currency_id,
                        months,
                        month_start,
                        month_end,
                        working_day,
                        total_project_expense,
                        operation_cost,
                        average_cost_company,
                        average_cost_project,
                        members,
                        all_members,
                        total_salary,
                        profit,
                        profit_margin,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    project_management_id,
                    currency_id,
                    months,
                    month_start,
                    month_end,
                    working_day,
                    total_project_expense,
                    operation_cost,
                    average_cost_company,
                    average_cost_project,
                    members,
                    all_members,
                    total_salary,
                    profit,
                    profit_margin,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_management_history;
       
            """
         
            
    def query_project_management_member(self, user_update):
        return """
                DELETE FROM project_management_member_data;
                INSERT INTO
                    project_management_member_data(
                        id,
                        project_management_id,
                        company_id,
                        employee_id,
                        job_id,
                        planning_role_id,
                        email,
                        number_phone,
                        start_date,
                        end_date,
                        member_type,
                        effort_rate,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    project_management_id,
                    company_id,
                    employee_id,
                    job_id,
                    planning_role_id,
                    email,
                    number_phone,
                    start_date,
                    end_date,
                    member_type,
                    effort_rate,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_management_member;
       
            """
            
    
    def query_project_management_member_detail(self, user_update):
        return """
                DELETE FROM project_management_member_detail_data;
                INSERT INTO
                    project_management_member_detail_data(
                        id,
                        project_members,
                        employee_id,
                        currency_id,
                        month_start,
                        month_end,
                        effort_rate,
                        working_day,
                        man_month,
                        total_members,
                        months,
                        average_cost_company,
                        average_cost_project,
                        salary,
                        profit,
                        average_profit,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    project_members,
                    employee_id,
                    currency_id,
                    month_start,
                    month_end,
                    effort_rate,
                    working_day,
                    man_month,
                    total_members,
                    months,
                    average_cost_company,
                    average_cost_project,
                    salary,
                    profit,
                    average_profit,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_management_member_detail;
       
            """
    
    
    def query_department_project_detail(self, user_update):
        return """
                DELETE FROM department_project_detail_data;
                INSERT INTO
                    department_project_detail_data(
                        id,
                        project_management_id,
                        company_id,
                        project_id,
                        department_id,
                        user_pm,
                        currency_id,
                        months,
                        month_start,
                        month_end,
                        working_day,
                        total_members,
                        total_salary,
                        total_project_cost,
                        total_revenue,
                        total_profit,
                        profit_margin,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    project_management_id,
                    company_id,
                    project_id,
                    department_id,
                    user_pm,
                    currency_id,
                    months,
                    month_start,
                    month_end,
                    working_day,
                    total_members,
                    total_salary,
                    total_project_cost,
                    total_revenue,
                    total_profit,
                    profit_margin,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM department_project_detail;
       
            """
             
             
    def query_project_management_subceo(self, user_update):
        return """
                DELETE FROM project_management_subceo_data;
                INSERT INTO 
                    project_management_subceo_data(
                        id,
                        company_id,
                        department_id,
                        currency_id,
                        months,
                        month_start,
                        month_end,
                        total_members,
                        total_salary,
                        total_project_cost,
                        total_revenue,
                        total_profit,
                        profit_margin,
                        user_login,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    company_id,
                    department_id,
                    currency_id,
                    months,
                    month_start,
                    month_end,
                    total_members,
                    total_salary,
                    total_project_cost,
                    total_revenue,
                    total_profit,
                    (CASE
                        WHEN total_revenue = 0
                            THEN 0
                        ELSE (total_profit / total_revenue) * 100
                    END) AS profit_margin,
                    user_login,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_management_subceo;
       
            """
             
             
    def query_project_management_ceo(self, user_update):
        return """
                DELETE FROM project_management_ceo_data;
                INSERT INTO
                    project_management_ceo_data(
                        id,
                        company_id,
                        representative,
                        currency_id,
                        months,
                        month_start,
                        month_end,
                        total_members,
                        total_salary,
                        total_project_cost,
                        total_revenue,
                        total_profit,
                        profit_margin,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    id,
                    company_id,
                    representative,
                    currency_id,
                    months,
                    month_start,
                    month_end,
                    total_members,
                    total_salary,
                    total_project_cost,
                    total_revenue,
                    total_profit,
                    (CASE
                        WHEN total_revenue = 0
                            THEN 0
                        ELSE (total_profit / total_revenue) * 100
                    END) AS profit_margin,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM project_management_ceo;
       
            """