# -*- coding: utf-8 -*-
{
    'name': 'Timesheet Updation',
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""" ,
    'category': 'Services/Timesheets' ,
    'author': 'thuanlv',
    'company': 'Dsoft',
    'depends': ['base', 'hr_timesheet'] ,
    'data': [
        'views/hr_timesheet_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_qweb': [
        ]
    },
    'images': [] ,
    'license': 'AGPL-3' ,
    'installable': True ,
    'application': False ,
}
