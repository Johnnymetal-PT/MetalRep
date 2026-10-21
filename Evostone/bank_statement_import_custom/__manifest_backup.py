{
    "name": "Bank Statement Import Custom",
    "version": "18.0.2.0.0",
    "category": "Accounting",
    "summary": "Advanced bank statement import with preview and validation",
    "description": """
        Enhanced bank statement import module for Odoo 18 with advanced features:
        
        ✅ Data Preview - View transactions before importing with option to show all
        ✅ Duplicate Detection - Automatic validation against existing transactions
        ✅ Visual Progress - Real-time progress bar and status messages
        ✅ Import Report - Comprehensive summary with statistics and logs
        ✅ Multi-Bank Support - BIM, BCI, and CARD formats
        ✅ Field Mapping - Customizable column mapping for non-standard formats
        ✅ Smart Parsing - Automatic format detection and data transformation
        
        Version 2.0.0 includes major UX improvements and validation features.
    """,
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "account_statement_base", 
        "account_reconcile_oca",
        "base_import",  
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/server_action.xml",
        "wizard/bank_statement_import_wizard_views.xml",
        "views/account_bank_statement_line_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bank_statement_import_custom/static/src/js/simple_interceptor.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}