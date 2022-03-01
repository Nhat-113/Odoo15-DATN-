{
    'name': 'HR Employee Disable Create Button',
    'summary': 'HR Employee Disable Create Button in Screen Detail Employee',
    'version': "1.1.0",
    'category': 'Human Resources',
    'author': 'vietlx',
    'website': 'https://d-soft.com.vn/',
    'license': 'AGPL-3',
    'depends': [
        'hr',
        'web',
        'hr_holidays'
    ],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}
