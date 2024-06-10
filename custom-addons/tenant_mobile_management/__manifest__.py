{
    'name': 'Tenant Mobile Management',
    'description': """Tenant Mobile Management""",
    'version': '1.0',
    'author': 'Vo Van Nhat',
    'category': 'Hidden',
    'depends': ['base', 'mail'],
    "assets": {
        "web.assets_backend": [
            "tenant_mobile_management/static/src/css/tenant_management.css",
            ],
    },
    'data': [
        'security/security.xml',
        'views/tenant_view.xml',

    ],
    'license': 'AGPL-3' ,
    'installable': True ,
    'application': False ,
    "auto_install": False,
}