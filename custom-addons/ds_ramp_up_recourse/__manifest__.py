{
    'name': "Resource Management",
    'version': '15.0.1.0.0',
    'summary': """""",
    'description': """""",
    'category': 'Services/Project',
    'live_test_url': '',
    'author': 'phuongtn',
    'company': 'Dsoft',
    'maintainer': '',
    'website': "",
    'depends': ['hr', 'base', 'project', 'ds_project_planning', 'project_updation'],
    'data': [
        'security/task_score_security.xml',
        'security/ir.model.access.csv',
        'views/ramp_up.xml',
        'report/ramp_up_project.xml',
        'views/task_score_view.xml',
        'views/ramp_up_menu.xml',
        'views/report_rampup_recourse_view.xml',
        'data/ramp_up_cron.xml' 
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
