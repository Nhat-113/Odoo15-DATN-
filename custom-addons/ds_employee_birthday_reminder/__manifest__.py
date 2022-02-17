{
    "name": "DS Employee Birthday Wish & Reminder",
    "version": "15.0.0.1.0",
    "category": "Human Resources",
    "summary": "Employee Birthday Wish & Reminder",
    "description": """
        Show notifications for Employees Birthday on current month in employees list
        Add This Month Filter Date of Birth in Employees list
        Send email Birthday Wish to Employee
        Send email Reminder To Manager for Birthday Wish
    """,
    "author": "nhannv",
    'website': 'https://d-soft.com.vn/',
    "depends": ["hr"],
    "license": "AGPL-3",
    "data": [
        "data/birthday_reminder_cron.xml",
        "data/mail_templates.xml",
        "data/ir_config_settings_data.xml",
        "views/res_config_settings_views.xml",
        "views/employee_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
