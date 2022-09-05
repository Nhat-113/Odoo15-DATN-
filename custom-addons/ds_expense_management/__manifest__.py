# -*- coding: utf-8 -*-
{
    'name': "Expenses Management",
    'summary': "Company Management Expenses",
    'author': "D-Soft",
    'website': "https://d-soft.com.vn",
    'category': 'Services/Expenses',
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    'depends': ['base', 'project', 'mail'],
    "application": True,
    'data': [
        "security/expense_management_security.xml",
        "security/ir.model.access.csv",
        "views/expense_management_menu.xml",
        "views/category_expense_view.xml",
        "views/general_expense_view.xml",
        "views/project_expense_view.xml",
        "views/project_project_view.xml",
        "views/project_revenue_view.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/ds_expense_management/static/src/css/style.css',
        ],
        'web.assets_qweb': [
        ]
    },
}
