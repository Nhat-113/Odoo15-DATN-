# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Request Over Time",
    "summary": """
        Module Request Over Time of D-soft company""",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "author": "Dientd",
    "website": "",
    'depends': ['base', 'project'],
    "development_status": "Alpha",
    "data": [
    "security/hr_request_overtime_security.xml",
    "security/ir.model.access.csv", 
    "data/hr_request_overtime_data.xml",
    "views/hr_timesheet_menu_view.xml",
    "views/hr_timesheet_request_overtime_view.xml"
    ],
}
