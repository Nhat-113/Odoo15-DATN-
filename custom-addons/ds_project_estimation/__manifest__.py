# -*- coding: utf-8 -*-
{
    'name': "Estimation",
    'summary': "Manage project plan",
    'author': "Quang Vinh",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Estimation',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['base'],
    "application": True,
    'data': [
        "views/estimation_menu.xml",
        "views/work_view.xml",
        "views/estimation_sequence.xml",
        "views/job_position_view.xml",
        "views/cost_rate_view.xml",
        "views/activity_view.xml",
        "views/description_view.xml",
        "views/project_type_view.xml",
        "views/currency_rate_view.xml",
        "security/estimation_security.xml",
        "security/ir.model.access.csv",
        "data/activity_data.xml",
        "data/project_type_data.xml",
        "data/job_position_data.xml",
        "data/summary_data.xml",
        "data/currency_rate_data.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'ds_project_estimation/static/src/css/style.css',
        ]
    },
}
