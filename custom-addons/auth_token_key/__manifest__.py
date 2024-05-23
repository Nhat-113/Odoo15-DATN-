{
    "name": "Auth Api Token",
    "summary": """
        Authenticate http requests from an API key""",
    "version": "15.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "development_status": "Beta",
    "depends": ["base"],
    "data": [
        "security/auth_token_security.xml",
        "security/ir.model.access.csv", 
        "views/auth_token_key.xml",
    ],
}
