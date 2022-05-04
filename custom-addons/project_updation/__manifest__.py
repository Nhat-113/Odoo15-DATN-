{
    'name': "Project Updation",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'category': 'Services/Project',
    'live_test_url': '',
    'author': 'phuongtn',
    'company': 'Dsoft',
    'maintainer': '',
    'website': "",
    'depends': ['hr', 'base', 'project', 'web_domain_field', 'ds_project_planning'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'views/project_view.xml',
        'security/ir.model.access.csv',
        'data/type_default.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_updation/static/src/lib/bootstrap-colorpicker/css/style.css',
        ],
        'web.assets_qweb': [
        ],
    },

    'images': ['project_updation/static/img/tick.png'],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}