def get_all_department_children(request, parent_id, list_departments):
    child_departments = request.env['hr.department'].search([('parent_id', 'in', parent_id)]).ids
    
    if child_departments:
        list_departments += child_departments
        return get_all_department_children(request, child_departments, list_departments)
    else:
        return list_departments