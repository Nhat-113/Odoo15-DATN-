def get_children_departments(self, department_id):
    children_departments = []
    
    direct_children = self.env['hr.department'].search([('parent_id', '=', department_id)]).ids
    
    for child in direct_children:
        children_departments.append(child)
        children_departments.extend(get_children_departments(self, child))
    return children_departments
    

def get_sql_by_department(self):
    current_user = self.env.user
    sql_domain_parent_department = ''
    departments = get_children_departments(self, current_user.department_id.id)
    departments.append(current_user.department_id.id)
        
    if len(departments) > 1:
        sql_domain_parent_department ='' + 'and department_id in ' + str(tuple(departments)) + ')'
    elif len(departments) == 1:
        sql_domain_parent_department = '' + 'and department_id = ' + str(departments[0]) + ')'
    else:
        sql_domain_parent_department = ''
    return sql_domain_parent_department