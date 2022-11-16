# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Request Over Time",
    "summary": """
        Module Request Over Time of D-soft Company""",
    "version": "15.0.1.0.0",
    'category': 'Services/Timesheet Overtime',
    "license": "LGPL-3",
    "author": "Dientd",
    "website": "",

    'depends': ['base', 
                'project',
                'hr_timesheet',
                'mail', 'project_updation'],

    'assets': {
        'web.assets_backend': [
            '/hr_timesheet_request_overtime/static/src/css/style.css',
        ],
    },

    "development_status": "Alpha",

    "data": [
            "security/hr_request_overtime_security.xml",
            "security/ir.model.access.csv",
            "wizard/hr_request_overtime_refuse_reason_views.xml",
            "data/hr_request_overtime_data.xml",
            "data/mail_template.xml",
            "views/hr_timesheet_menu_view.xml",
            "views/hr_timesheet_request_overtime_view.xml",
            "views/hr_timesheet_reporting_overtime.xml"
            ],
}
