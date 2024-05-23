# -*- coding: utf-8 -*-
{
    "name": "Invoice Converting",
    "summary": """
        Invoice and transaction converting""",
    "description": """
        Invoice and transaction converting
    """,
    "author": "Dung Vo",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["base"],
    "assets": {
        "web.assets_backend": [
            "converting/static/src/css/converting.css",
            "converting/static/src/js/field.js",
        ],
    },
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/converting_views.xml",
        "views/menu.xml",
    ],
    "sequence": -100,
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
