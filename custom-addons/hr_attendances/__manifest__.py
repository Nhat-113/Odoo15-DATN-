# -*- coding: utf-8 -*-
{
    'name': "HR Attendances",
    'summary': "Attendances with Face log",
    'author': "Dientd",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Hr_attendances',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['hr', 'report_xlsx', 'mail', 'hr_attendance', "auth_token_key"],
    "application": True,
    'data': [
        # 'security/hr_attendance_security.xml',
        'security/ir.model.access.csv',
        'views/export_wizard_form_view.xml',
        # 'views/hr_attendance_report_xlsx.xml',
        # 'data/attendance_mising_mail_template.xml',
        # 'data/hr_attendance_missing_cron.xml',
        'data/hr_attendance_cron.xml',
        'views/hr_attendance_menu.xml',
        # 'views/hr_attendance_missing_view.xml',
        'views/mail_template_notification.xml',
        'views/attendance_calendar_view.xml',
        'views/hr_attendance_pesudo_view.xml',
        'views/hr_attendance_view.xml',
        'views/hr_employee_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/hr_attendances/static/src/js/export_excel_view.js',
            '/hr_attendances/static/src/js/export_excel_report_action.js'
        ],
        'web.assets_qweb': [
           '/hr_attendances/static/src/xml/export_excel_view.xml'
        ]
    }
}
