{
    'name': "Planning Gantt",

    'summary': """
        This module integrates project tasks with the interactive HTML5 Gantt chart
        from DHX. Their website is https://dhtmlx.com""",
    
        'assets': {
            'web.assets_backend': [
                '/dhx_gantt/static/lib/dhtmlxgantt/js/dhtmlxgantt.js',
                '/dhx_gantt/static/lib/dhtmlxgantt/js/dhtmlxgantt_marker.js',
                '/dhx_gantt/static/lib/dhtmlxgantt/skins/dhtmlxgantt_material.css',
                '/dhx_gantt/static/lib/dhtmlxgantt/css/dhtmlxgantt.css',
                '/dhx_gantt/static/src/js/gantt_model.js',
                '/dhx_gantt/static/src/js/gantt_renderer.js',
                '/dhx_gantt/static/src/js/gantt_controller.js',
                '/dhx_gantt/static/src/js/gantt_view.js',
                '/dhx_gantt/static/src/js/gantt_action.js',

                '/dhx_gantt/static/src/css/gantt.css',
                '/dhx_gantt/static/src/css/custom.css'

            ],
            'web.assets_qweb': [
                'dhx_gantt/static/src/xml/gantt.xml'
            ],
        },

    "category": "Project Management",

    'author': "hieutl",
    'website': "https://d-soft.com.vn/",
    'license': "GPL-3",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Planning Project Management',
    'version': '0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'project'
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/task_views.xml',
        'views/project_views.xml',
    ],
    'images': [
        'images/gantt-preview.png'
    ],
    'uninstall_hook': 'dhx_uninstall_hook'
}
