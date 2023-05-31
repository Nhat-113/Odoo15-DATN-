# -*- coding: utf-8 -*-
{
    'name': "HR Attendances",
    'summary': "Attendances with Face log",
    'author': "Dientd",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Hr_attendances',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['hr', 'hr_holidays', 'resource', 'report_xlsx', 'mail'],
    "application": True,
    'data': [
        'security/hr_attendance_security.xml',
        'security/ir.model.access.csv',
        'views/hr_attendance_report_xlsx.xml',
        'data/attendance_mising_mail_template.xml',
        'data/hr_attendance_missing_cron.xml',
        'data/hr_attendance_cron.xml',
        'views/hr_attendance_missing_view.xml',
        'views/mail_template_notification.xml',
        'views/attendance_calendar_view.xml',
    ],
    'assets': {
        'web.assets_backend': [

        ],
        'web.assets_qweb': [
           
        ]
    },
}
