{
    "name": "DS Print Contract",
    "version": "15.0.1.0.0",
    "category": "Human Resources",
    'author': 'nhannv',
    'website': 'https://d-soft.com.vn/',
    "license": "AGPL-3",
    "summary": """Print Contract Detail for the employee.""",
    "depends": ["hr", "hr_contract", "hr_employee_updation"],
    "data": ["views/contract_report.xml", "report/contract_qweb_report.xml"],
    "installable": True,
    'auto_install': False,
    'application': False,
}
