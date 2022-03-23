{
    'name': 'Mail Templates',
    'summary': 'Replace keyword Odoo equals D-Soft',
    'version': "1.1.0",
    'category': 'Human Resources',
    'author': 'vietlx',
    'website': 'https://d-soft.com.vn/',
    'license': 'AGPL-3',
    'depends': [
        'mail'
    ],
    'data': [
        'data/mail_templates.xml',
        'views/disable_button_save_as_template_views.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}
