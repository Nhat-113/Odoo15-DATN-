{
    'name': "Project Updation",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'category': 'Generic Modules/Services',
    'live_test_url': '',
    'author': 'phuongtn',
    'company': 'Dsoft',
    'maintainer': '',
    'website': "",
    'depends': ['hr', 'base', 'project'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'views/project_view.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'project_updation/static/src/lib/bootstrap-colorpicker/css/style.css',
            # 'project_updation/static/src/lib/bootstrap-colorpicker/css/bootstrap-colorpicker.css',
            # 'project_updation/static/src/js/widget.js',
            # 'project_updation/static/src/lib/bootstrap-colorpicker/js/bootstrap-colorpicker.js',
        ],
        'web.assets_qweb': [
            # 'project_updation/static/src/xml/widget.xml',
        ],
    },

    'images': ['project_updation/static/img/tick.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}