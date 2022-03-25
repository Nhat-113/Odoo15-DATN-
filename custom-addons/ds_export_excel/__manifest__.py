{
    'name': "DS Export Excel Report",
    'version': '15.0.1.0.0',
    'summary': """Export excel payslips report""",
    'description': """This module allow to export xlsx Payslips report""",
    'author': "nhannv",
    'company': "D-Soft",
    'website': "http://d-soft.com.vn",
    'category': 'Human Resources',
    'depends': ['report_xlsx', 'hr', 'hr_payroll_community'],
    'data': [
        'views/report_payslip_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
