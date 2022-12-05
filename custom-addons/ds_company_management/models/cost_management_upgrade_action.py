from odoo import models, fields, api


class DepartmentMiraiFnb(models.Model):
    _name = 'department.mirai.fnb'
    _Description = 'Table is store id data department Mirai FnB'
        
    department_id = fields.Many2one('hr.department', string='Department Mirai Fnb')


class UpgradeAction(models.Model):
    _name = 'cost.management.upgrade.action'
    
    
    def handle_remove_department(self):
        mirai_fnb_department_id = self.env['hr.department'].sudo().search([('name', '=', 'Mirai FnB')])
        department_ids = self.get_all_department_children(mirai_fnb_department_id.ids, [])
        department_ids += mirai_fnb_department_id.ids
        return department_ids
    
    def get_all_department_children(self, parent_id, list_departments):
        child_departments = self.env['hr.department'].sudo().search([('parent_id', 'in', parent_id)])
        
        if child_departments:
            list_departments += child_departments.ids
            return self.get_all_department_children(child_departments.ids, list_departments)
        else:
            return list_departments
    
    
    @api.model
    def cost_management_reset_update_data(self):
        department_ids = self.handle_remove_department()
        self.env['department.mirai.fnb'].sudo().search([]).unlink()
        if len(department_ids) > 0:
            for dp_id in department_ids:
                self.env['department.mirai.fnb'].create({'department_id': dp_id})
                
        user_update = str(self.env.user.id)
        all_query = self.query_delete_project_expense_value_generate() +\
                    self.query_available_booking_employee(user_update) +\
                    self.query_project_management(user_update) +\
                    self.query_project_management_history(user_update) +\
                    self.query_project_management_member(user_update) +\
                    self.query_project_management_member_detail(user_update) +\
                    self.query_department_project_detail(user_update) +\
                    self.query_project_management_ceo(user_update) +\
                    self.query_project_management_subceo(user_update)

        self.env.cr.execute(all_query)
        
        # get default project_management_id for project cost management [Company expense]
        project_expenses = self.env['project.expense.value'].sudo().search([('project_id', '!=', False), ('department_id', 'not in', department_ids)])
        project_managements = self.env['project.management.data'].sudo().search([('project_id', 'in', project_expenses.project_id.ids)])
        
        department_expenses = self.env['project.expense.value'].sudo().search([('project_id', '=', False), ('department_id', 'not in', department_ids)])
        project_departments = self.env['project.management.data'].sudo().search([('department_id', 'in', department_expenses.department_id.ids)]) #, ('stage_name', '!=', 'Done')
        for record in project_expenses:
            for pm in project_managements:
                if record.project_id.id == pm.project_id.id:
                    record.project_management_id = pm.id
                    
        for pm in project_departments:
            for expense in department_expenses:
                if expense.department_id.id == pm.department_id.id:
                    if expense.expense_date >= pm.project_id.date_start and expense.expense_date <= pm.project_id.date:
                        cnt = self.compute_count_project_department_expense(project_departments, expense.department_id.id, expense.expense_date)
                        # cnt = sum(1 for prj in project_departments if expense.expense_date >= prj.project_id.date_start and expense.expense_date <= prj.project_id.date)
                        vals = {
                            'name': expense.name,
                            'expense_date': expense.expense_date,
                            'total_expenses': expense.total_expenses / cnt,
                            'exchange_rate': expense.exchange_rate,                    
                            'expense_vnd': expense.exchange_rate * expense.total_expenses / cnt
                        }
                        
                        vals_update = {
                            'project_management_id': pm.id,
                            'currency_id': expense.currency_id.id,
                            'currency_vnd': expense.currency_vnd.id,
                            'project_id': pm.project_id.id,
                            'department_id': pm.department_id.id
                        }
                        
                        #because project_expense_value, fields in vals_update using related with project_expense_management,
                        # so can't create them -> using write method to update them
                        result = self.env['project.expense.value'].sudo().create(vals)
                        result.sudo().write(vals_update)
        
        return
        # return {'type': 'ir.actions.client', 'tag': 'reload'}
        
        
    def compute_count_project_department_expense(self, projects, department_id, expense_date):
        cnt = 0
        for prj in projects:
            if prj.department_id.id == department_id \
                and expense_date >= prj.project_id.date_start \
                and expense_date <= prj.project_id.date:
                    cnt += 1
        return cnt

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
                        stage_id,
                        stage_name,
                        count_members, 
                        total_salary, 
                        profit, 
                        project_cost,
                        total_avg_operation_project,
                        total_department_expense, 
                        revenue, 
                        total_commission,
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
                    stage_id,
                    stage_name,
                    phg.total_members AS count_members,
                    phg.total_salary AS total_salary,
                    phg.total_profit AS profit,
                    phg.total_project_expense AS project_cost,
                    phg.total_avg_operation_project,
                    phg.total_department_expense,
                    pm.revenue,
                    pm.total_commission,
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
                    ON phg.project_id = pm.project_id;
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
                        months_domain,
                        month_start,
                        month_end,
                        working_day,
                        total_project_expense,
                        total_department_expense,
                        operation_cost,
                        average_cost_company,
                        average_cost_project,
                        total_avg_operation_project,
                        members,
                        members_project_not_intern,
                        all_members,
                        total_salary,
                        revenue,
                        total_commission,
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
                    months_domain,
                    month_start,
                    month_end,
                    working_day,
                    total_project_expense,
                    total_department_expense,
                    operation_cost,
                    average_cost_company,
                    average_cost_project,
                    total_avg_operation_project,
                    members,
                    members_project_not_intern,
                    all_members,
                    total_salary,
                    revenue,
                    total_commission,
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
                        months_domain,
                        month_start,
                        month_end,
                        working_day,
                        total_members,
                        total_salary,
                        total_project_cost,
                        total_department_expense,
                        total_revenue,
                        total_commission,
                        total_avg_operation_project,
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
                    months_domain,
                    month_start,
                    month_end,
                    working_day,
                    total_members,
                    total_salary,
                    total_project_cost,
                    total_department_expense,
                    total_revenue,
                    total_commission,
                    total_avg_operation_project,
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
                        total_avg_operation_department,
                        total_project_cost,
                        total_department_cost,
                        total_revenue,
                        total_commission,
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
                    total_avg_operation_department,
                    total_project_cost,
                    total_department_cost,
                    total_revenue,
                    total_commission,
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
                        currency_id,
                        months,
                        month_start,
                        month_end,
                        total_members,
                        total_salary,
                        total_project_cost,
                        total_department_cost,
                        total_avg_operation_company,
                        total_revenue,
                        total_commission,
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
                    currency_id,
                    months,
                    month_start,
                    month_end,
                    total_members,
                    total_salary,
                    total_project_cost,
                    total_department_cost,
                    total_avg_operation_company,
                    total_revenue,
                    total_commission,
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
            
    def query_available_booking_employee(self, user_update):
        return """
                DELETE FROM available_booking_employee_data;
                INSERT INTO
                    available_booking_employee_data(
                        --id,
                        company_id,
                        department_id,
                        employee_id,
                        currency_id,
                        months,
                        months_str,
                        salary,
                        available_salary,
                        available_mm,
                        available_effort,
                        create_uid,
                        write_uid,
                        create_date,
                        write_date
                    )
                SELECT
                    --id,
                    company_id,
                    department_id,
                    employee_id,
                    currency_id,
                    months,
                    months_str,
                    salary,
                    available_salary,
                    available_mm,
                    available_effort,
                    """ + user_update + """,
                    """ + user_update + """,
                    CURRENT_DATE,
                    CURRENT_DATE
                FROM available_booking_employee;
            """
            
            
    def query_delete_project_expense_value_generate(self):
        return """
            DELETE FROM project_expense_value 
                    WHERE project_expense_management_id IS NULL;
            """