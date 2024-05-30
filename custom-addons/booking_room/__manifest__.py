# -*- coding: utf-8 -*-
{
    "name": "Booking Room",
    "summary": """
      Booking Room""",
    "description": """
        Booking Room
    """,
    "author": "Odoo Intern",
    "website": "https://d-soft.com.vn",
    "category": "Uncategorized",
    "version": "0.1",
    "depends": ["mail","calendar"],
    "assets": {
        "web.assets_backend": [
            "booking_room/static/src/css/booking_room.css",
            "booking_room/static/src/js/year_calendar_view.js",
            "booking_room/static/src/js/booking_popover.js",
            "booking_room/static/src/js/list.js",
            "booking_room/static/src/js/msm.js",
            "booking_room/static/src/xml/delete_event.xml",
            "booking_room/static/src/xml/calendar_popover.xml",
        ],
        'web.assets_qweb': [
            'booking_room/static/src/xml/delete_event.xml',
            "booking_room/static/src/xml/calendar_popover.xml",
        ],
    },
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/room_view.xml",
        "views/schedule_view.xml",
        "views/menu.xml",
        "data/mail_template.xml",
        "data/edit_event_mail.xml"
      
    ],
    "sequence": -100,
    "installable": True,
    "application": True,
    "auto_install": False,
    "license": "LGPL-3",
}
