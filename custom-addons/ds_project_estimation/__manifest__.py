# -*- coding: utf-8 -*-
{
    'name': "Estimation",
    'summary': "Manage project plan",
    'author': "Quang Vinh",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Estimation',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['base','sale','web'],
    "application": True,
    'data': ["views/estimation_menu.xml",
            "views/work_view.xml",
            "views/estimation_sequence.xml",
            
            "security/estimation_security.xml",
            "security/ir.model.access.csv",],
}
