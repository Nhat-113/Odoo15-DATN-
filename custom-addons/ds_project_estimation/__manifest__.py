# -*- coding: utf-8 -*-
{
    'name': "Estimation",
    'summary': "Manage project plan",
    'author': "Quang Vinh, VietLX",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Estimation',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['base', 'crm'], #, 'web_domain_field'
    "application": True,
    'data': [
        "security/estimation_security.xml",
        "security/ir.model.access.csv",
        "data/currency_data.xml",
        "data/activity_data.xml",
        "data/project_type_data.xml",
        "data/job_position_data.xml",
        "data/module_summary_data.xml",
        "data/cost_rate_data.xml",
        "views/estimation_menu.xml",
        "views/gantt_resource_planning.xml",
        "views/work_view.xml",
        "views/estimation_sequence.xml",
        "views/job_position_view.xml",
        "views/cost_rate_view.xml",
        "views/activity_view.xml",
        "views/project_type_view.xml",
        "data/gen_project_cron.xml",
        "wizard/message_wizard_views.xml"

    ],
    'assets': {
        'web.assets_backend': [
            '/ds_project_estimation/static/src/css/style.css',
            '/ds_project_estimation/static/lib/dhtmlxgantt/js/dhtmlxgantt.js',
            '/ds_project_estimation/static/lib/dhtmlxgantt/js/api.js',
            '/ds_project_estimation/static/lib/dhtmlxgantt/js/dhtmlxgantt_marker.js',
            '/ds_project_estimation/static/lib/dhtmlxgantt/skins/dhtmlxgantt_material.css',
            '/ds_project_estimation/static/lib/dhtmlxgantt/css/dhtmlxgantt.css',
            '/ds_project_estimation/static/src/js/gantt_model.js',
            '/ds_project_estimation/static/src/js/gantt_renderer.js',
            '/ds_project_estimation/static/src/js/gantt_controller.js',
            '/ds_project_estimation/static/src/js/gantt_view.js',
            '/ds_project_estimation/static/src/js/gantt_action.js',
            '/ds_project_estimation/static/src/css/gantt.css'
        ],
        'web.assets_qweb': [
            'ds_project_estimation/static/src/xml/gantt.xml'
        ]
    },
}
