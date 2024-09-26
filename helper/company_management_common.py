from helper.helper import get_children_departments

def get_sql_by_department(self):
    current_user = self.env.user
    empl_id = current_user.employee_id.id
    sql_domain_parent_department = ' and department_id = null) '
    if empl_id:
        managing_departments = self.env['hr.department'].search([('manager_id', '=', empl_id)])
        if managing_departments:
            managing_departments_ids = managing_departments.ids
            departments = get_children_departments(self, managing_departments_ids)
            departments.extend(managing_departments_ids)
                
            if len(departments) > 1:
                sql_domain_parent_department = ' and department_id in ' + str(tuple(departments)) + ') '
            elif len(departments) == 1:
                sql_domain_parent_department = ' and department_id = ' + str(departments[0]) + ') '
    return sql_domain_parent_department

def is_ceo(current_user):
    return current_user.has_group('ds_company_management.group_company_management_ceo')

def is_sub_ceo(current_user):
    return current_user.has_group('ds_company_management.group_company_management_sub_ceo')

def is_div_manager(current_user):
    return current_user.has_group('ds_company_management.group_company_management_div')
    
def is_group_leader(current_user):
    return current_user.has_group('ds_company_management.group_company_management_group_leader')