# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Facelog Box Register",
    "version": "1.0.0",
    "category": "Services",
    "author": "Khoa Huynh",
    "sequence": -100,
    "summary": "Facelog box management",
    "description": """
        Facelog box management
    """,
    "depends": ["base", "hr_attendances", "hr_attendance"],
    "data": [
        "security/box_management.xml",
        "security/ir.model.access.csv",
        "views/passcode_register_view.xml",
        "views/box_management_view.xml",
        "views/setting_device_view.xml",
        "views/menu.xml",
        "views/hr_attendance_view.xml",
        "views/hr_attendance_pseudo_view.xml",
        "views/res_config_setttings.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",
    "assets": {},
}