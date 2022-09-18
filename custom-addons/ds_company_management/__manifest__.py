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
    'depends': ['hr', 
                'mail', 
                'base', 
                'project', 
                'ds_project_planning', 
                'project_updation', 
                'hr_employee_updation', 
                'ds_employee_seniority', 
                'ds_project_estimation',
                'ds_expense_management'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_history_project_management.xml',
        'data/exchange_rate_api_data.xml',
        'views/project_project_view.xml',
        'views/exchange_rate_view.xml',
        'views/human_resource_management_view.xml',
        'views/project_management_view.xml',
        'views/company_management_menu.xml',
        'views/project_expense_management_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/ds_company_management/static/src/css/style.css'
        ],
        'web.assets_qweb': [
           
        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
