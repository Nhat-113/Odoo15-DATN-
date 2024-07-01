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
    'depends': ['base'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'views/asset_view.xml',
        'views/device_view.xml',
        'views/device_iaq_view.xml',
        'views/device_lc_view.xml',
        'views/device_lc_schedule_view.xml',
        'views/smo_menu.xml',
        'views/res_config_settings_views.xml',

        'data/cronjob.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'smo/static/src/js/custom_list_view.js',
            'smo/static/src/js/devices_list_view_renderer.js'
        ],
        'web.assets_qweb': [
        ],
    },
    # 'images': ["static/description/banner.png"],
    'license': "LGPL-3",
    'installable': True,
    'application': True,
}
