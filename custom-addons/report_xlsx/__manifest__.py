{
    "name": "Base report xlsx",
    "summary": "Base module to create xlsx report",
    "author": "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/reporting-engine",
    "category": "Reporting",
    "version": "15.0.1.0.4",
    "development_status": "Production/Stable",
    "license": "AGPL-3",
    "external_dependencies": {"python": ["xlsxwriter", "xlrd"]},
    "depends": ["base", "web"],
    "demo": ["demo/report.xml"],
    "installable": True,
    "assets": {
        "web.assets_backend": [
            "report_xlsx/static/src/js/report/action_manager_report.esm.js",
        ],
    },
}
