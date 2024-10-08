{
    'name': "Smart Office",
    'version': '1.0.0',
    'summary': """
        Smart Office
    """,
    'description': """
        Help to control office devices
    """,
    'category': 'Services',
    'author': 'D-Soft Enterprise Team',
    'company': 'D-Soft',
    'maintainer': 'D-Soft Enterprise Team',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/asset_view.xml',
        'views/device_view.xml',
        'views/device_iaq_view.xml',
        'views/device_lc_view.xml',
        'views/device_lc_schedule_view.xml',
        'views/device_ac_view.xml',
        'views/dashboard.xml',
        'views/smo_menu.xml',
        'views/res_config_settings_views.xml',

        'data/cronjob.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'smo/static/src/js/devices_list_view_renderer.js',
            'smo/static/src/js/custom_list_view.js',
            'smo/static/src/js/devices_form_view_renderer.js',
            'smo/static/src/js/custom_form_view.js',
            'smo/static/src/js/ac_device_list_view_renderer.js',
            'smo/static/src/js/ac_device_list_view.js',
            'smo/static/src/js/lc_schedule_list_view.js',
            'smo/static/src/js/websocket_service.js',
            'smo/static/src/js/dashboard.js',
        ],
        'web.assets_qweb': [
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': "LGPL-3",
    'installable': True,
    'application': True,

}
