{
    'name': "Company Management",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'category': 'Services/Project',
    'live_test_url': '',
    'author': 'dsoft',
    'company': 'Dsoft',
    'maintainer': '',
    'website': "",
    'depends': ['hr', 'base', 'project', 'ds_project_planning', 'project_updation', 'hr_employee_updation', 'ds_employee_seniority'],
    'data': [
        'views/human_resource_management_view.xml',
        'views/company_management_menu.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_qweb': [
           
        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
