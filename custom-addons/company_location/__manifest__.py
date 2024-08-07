# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    "name": "Company Location",
    "version": "1.0.0",
    "category": "Services",
    "author": "Gia Duy",
    "sequence": -100,
    "summary": "Company Location",
    "description": """
        Company Location management
    """,
    "depends": ["base", "hr_attendances", "hr_attendance", "googlemap", "box_management"],
    "data": [
        "security/company_location.xml",
        "security/ir.model.access.csv",
        "views/company_location_view.xml",
        "views/res_config_settings.xml",
        "views/menu.xml"
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
    "license": "LGPL-3",
}