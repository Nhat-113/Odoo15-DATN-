def get_children_departments(self, department_id):
    children_departments = []
    
    direct_children = self.env['hr.department'].search([('parent_id', '=', department_id)]).ids
    
    for child in direct_children:
        children_departments.append(child)
        children_departments.extend(get_children_departments(self, child))
    return children_departments
    

def get_sql_by_department(self):
    current_user = self.env.user
    empl_id = current_user.employee_id.id
    sql_domain_parent_department = ' and department_id = null) '
    if empl_id:
        is_department_manager = empl_id == current_user.department_id.manager_id.id
        if is_department_manager:
            departments = get_children_departments(self, current_user.department_id.id)
            departments.append(current_user.department_id.id)
                
            if len(departments) > 1:
                sql_domain_parent_department = ' or department_id in ' + str(tuple(departments)) + ') '
            elif len(departments) == 1:
                sql_domain_parent_department = ' or department_id = ' + str(departments[0]) + ') '
    return sql_domain_parent_department

def is_ceo(current_user):
    return current_user.has_group('ds_company_management.group_company_management_ceo')

def is_sub_ceo(current_user):
    return current_user.has_group('ds_company_management.group_company_management_sub_ceo')

def is_div_manager(current_user):
    return current_user.has_group('ds_company_management.group_company_management_div')
    
def is_group_leader(current_user):
    return current_user.has_group('ds_company_management.group_company_management_group_leader')