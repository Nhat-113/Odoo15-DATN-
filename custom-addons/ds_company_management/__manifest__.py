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
                'ds_project_estimation',
                'ds_expense_management'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_reset_upgrade_exchange_rate_api.xml',
        'data/exchange_rate_api_data.xml',
        'views/exchange_rate_view.xml',
        # 'views/human_resource_management_view.xml',
        'views/project_management_view.xml',
        'views/project_management_subceo_view.xml',
        'views/project_management_ceo_view.xml',
        'views/department_project_detail_view.xml',
        'views/project_management_member_detail_view.xml',
        'views/company_management_menu.xml',
        'views/project_expense_management_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/ds_company_management/static/src/css/style.css',
            '/ds_company_management/static/src/js/human_resource_view.js',
            'ds_company_management/static/src/js/lib/table2excel.js',
            '/ds_company_management/static/src/css/bom_dashboard.css',
            '/ds_company_management/static/src/js/lib/chart.js',
            '/ds_company_management/static/src/js/dynamic_dashboard.js',
        ],
        'web.assets_qweb': [
            'ds_company_management/static/src/xml/human_resource_view.xml',
            'ds_company_management/static/src/xml/dynamic_dashboard_view.xml',
        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
