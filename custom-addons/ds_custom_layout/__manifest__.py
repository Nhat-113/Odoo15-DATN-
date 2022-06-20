{
    'name': 'DS Custom Layout',
    'version': '15.0.1',
    "author": "thuanlv",
    "license": "AGPL-3",
    'category': 'web',
    'depends': [
        'hr',
    ],
    'summary': 'Custom Layout',
    'assets': {
        'web.assets_backend': [
            'ds_custom_layout/static/src/css/employee.css',
            'ds_custom_layout/static/src/css/project.css',
            'ds_custom_layout/static/src/css/recruitment.css',
        ],
    },
    'installable': True,
    'auto_install': False,
}