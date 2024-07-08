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
    'depends': ['hr', 'base', 'project', 'web_domain_field', 'ds_project_planning', 'sale_timesheet'],
    'data': [
        'security/hr_timesheet_security.xml',
        'views/project_view.xml',
        'views/report_timesheet_templates_update.xml',
        'security/ir.model.access.csv',
        'data/type_default.xml',
        'views/hr_timesheet_line_task.xml',
        'data/mail_templates.xml',
        'data/cron_job_update_status_project.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'project_updation/static/src/lib/bootstrap-colorpicker/css/style.css',
        ],
        'web.assets_qweb': [
        ],
    },

    'images': [],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}