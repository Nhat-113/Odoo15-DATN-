{
    'name': "Ramp Up Resource",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'category': 'Generic Modules/Services',
    'live_test_url': '',
    'author': 'phuongtn',
    'company': 'Dsoft',
    'maintainer': '',
    'website': "",
    'depends': ['hr', 'base', 'project', 'ds_project_planning'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'views/ramp_up.xml',
        'views/ramp_up_menu.xml',
        'views/report_rampup_recourse_view.xml'
    ],
    'assets': {
        'web.assets_backend': [
        ],
        'web.assets_qweb': [
           
        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': True,
}
