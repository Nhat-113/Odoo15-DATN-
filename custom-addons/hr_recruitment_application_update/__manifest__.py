{
    'name': 'HR Recruitment Applicant Update',
    'summary': 'Update flow recruitment for D-soft company',
    'version': "1.1.0",
    'category': 'Human Resources/Recruitment',
    'author': 'dientd',
    'website': 'https://d-soft.com.vn/',
    'license': 'AGPL-3',
    'depends': [
        'hr',
        'hr_recruitment',
        'calendar',
        'hr_recruitment_survey'
    ],
    'data': [
        'security/hr_recruitment_security.xml',
        'security/ir.model.access.csv',
        'views/hr_recruitment_views.xml',
        'data/hr_recruitment_data.xml',
        'data/mail_templates.xml',
        'views/hr_recruitment_menu.xml',
        'views/hr_job_views.xml',
        'views/applicant_refuse_reason_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'assets': {
        'web.assets_backend': [
            'hr_recruitment_application_update/static/src/css/style.css',
        ],
    },
}
