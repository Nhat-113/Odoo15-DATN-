{
    'name': 'Tenant Mobile Management',
    'description': """Tenant Mobile Management""",
    'version': '1.0',
    'author': 'D-soft',
    'category': 'Hidden',
    'depends': ['base', 'mail'],
    "assets": {
        "web.assets_backend": [
            "tenant_mobile_management/static/src/css/tenant_management.css",
            ],
    },
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/tenant_view.xml',

    ],
    'license': 'AGPL-3' ,
    'installable': True ,
    'application': False ,
    "auto_install": False,
}