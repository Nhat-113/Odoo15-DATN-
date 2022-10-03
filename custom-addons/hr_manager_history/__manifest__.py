# -*- coding: utf-8 -*-

###############################################################################
{
    'name': 'History Department',
    'version': '15.0.1.0.0',
    'summary': """Adding Advanced Fields In Employee Master""",
    'description': '',
    'category': 'Generic Modules/Human Resources',
    'author': 'dientd',
    'company': 'D-soft Company',
    'website': "",
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_department_history_views.xml',
        'views/hr_company_history_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
           
        ],
        'web.assets_qweb': [
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
