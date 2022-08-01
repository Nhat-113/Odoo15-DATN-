{
    'name': 'Time Off Update',
    'version': '1.5',
    'category': 'Human Resources/Time Off',
    'sequence': 85,
    'summary': 'Allocate PTOs and follow leaves requests',
    'website': 'https://www.odoo.com/app/time-off',
    'author': 'phuongtn',
    'company': 'Dsoft',
    'description': """""",
    'depends': ['hr', 'base', 'hr_holidays', 'resource'],
    'data': [
        'data/hr_holidays_update_data.xml',
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
    'application': False,
}
