{
    'name': 'DS Employee Seniority',
    'summary': 'Display to Export Seniority of Employee',
    'version': "15.0.0.1.0",
    'category': 'Human Resources',
    'author': 'nhannv',
    'website': 'https://d-soft.com.vn/',
    'license': 'AGPL-3',
    'depends': [
        'hr',
        'hr_contract',
        'hr_employee_updation',
    ],
    'data': [
        'views/employee_views.xml',
        'data/employee_seniority_cron.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
