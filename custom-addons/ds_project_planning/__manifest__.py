{
    "name": "DS Project Planning",
    "version": "15.0.1.0.0",
    "description": "",
    "summary": "Manage project plan",
    'assets': {
        'web.assets_backend': [
            '/ds_project_planning/static/lib/dhtmlxgantt/js/dhtmlxgantt.js',
            '/ds_project_planning/static/lib/dhtmlxgantt/js/api.js',
            '/ds_project_planning/static/lib/dhtmlxgantt/js/dhtmlxgantt_marker.js',
            '/ds_project_planning/static/lib/dhtmlxgantt/skins/dhtmlxgantt_material.css',
            '/ds_project_planning/static/lib/dhtmlxgantt/css/dhtmlxgantt.css',
            '/ds_project_planning/static/src/js/gantt_model.js',
            '/ds_project_planning/static/src/js/gantt_renderer.js',
            '/ds_project_planning/static/src/js/gantt_controller.js',
            '/ds_project_planning/static/src/js/gantt_view.js',
            '/ds_project_planning/static/src/js/gantt_action.js',
            '/ds_project_planning/static/src/css/gantt.css'
        ],
        'web.assets_qweb': [
            'ds_project_planning/static/src/xml/gantt.xml'
        ],
    },
    'external_dependencies': {
        'python': ['pandas'],
    },
    "author": "Dsoft",
    "website": "https://d-soft.com.vn",
    "category": "Project",
    "license": "AGPL-3",
    "depends": ['base', 'project', 'mail', 'web_domain_field'],
    "application": True,
    "auto_install": False,
    "data": [
        "security/planning_security.xml",
        "security/ir.model.access.csv",
        "views/planning_views.xml",
        "views/planning_menu.xml",
        "views/project_task_views.xml",
        "views/project_menu.xml",
        "views/project_gantt_views.xml",
        "views/task_gantt_views.xml",
        "data/member_type_data.xml",
        "data/con_gen_update_week_month.xml",
        "views/project_update_status.xml",
    ],
}
