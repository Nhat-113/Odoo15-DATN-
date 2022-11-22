{
    'name': "Support Services",
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
                'web_domain_field'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/support_service_view.xml',
        'views/department_it_hr_view.xml',
        'views/support_service_menu.xml',
        'data/mail_template.xml',
        'data/department_it_hr_default.xml',
        'data/category_data_default.xml',
        'wizard/hr_request_service_refuse_reason_views.xml',
        'data/payment_data_default.xml',
        'data/status_data_default.xml'
    ],
    'assets': {
        'web.assets_backend': [
           '/ds_support_services/static/src/css/style.css'
        ],
        'web.assets_qweb': [

        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}