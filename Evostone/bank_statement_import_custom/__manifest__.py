{
    "name": "Bank Statement Import Custom",
    "version": "18.0.18.0.0",
    "category": "Accounting",
    "summary": "Advanced bank statement import with custom chart of accounts",
    "description": """
        Enhanced bank statement import module for Odoo 18 with advanced features:
        
        ✅ Data Preview - View transactions before importing with option to show all
        ✅ Duplicate Detection - Automatic validation against existing transactions
        ✅ Visual Progress - Real-time progress bar and status messages
        ✅ Import Report - Comprehensive summary with statistics and logs
        ✅ Multi-Bank Support - BIM, BCI, and CARD formats
        ✅ Field Mapping - Customizable column mapping for non-standard formats
        ✅ Smart Parsing - Automatic format detection and data transformation
        ✅ Custom Chart of Accounts - Customizable chart with code, name, partner limit and country
        
        Version 4.0.0: Custom chart of accounts model with enhanced fields.
        Version 3.0.0: Added support for multiple charts of accounts per company.
        Version 2.1.0: Migrated to use account_accountant module (Odoo official).
        Version 2.0.0: Major UX improvements and validation features.
    """,
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "license": "LGPL-3",
    "depends": [
        "account",
        "account_accountant",
        "base_import", 
        "contacts" 
    ],
    "data": [
        # Security
        "security/ir.model.access.csv",
        
        # Data
        "data/server_action.xml",
        
        # Views
        "views/company_chart_account_views.xml",
        
        # Wizards (must be loaded before views that reference them)
        "wizard/bank_statement_import_wizard_views.xml",
        "wizard/company_chart_account_wizard_views.xml",
        
        # Views that reference wizards
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/res_partner_tree_views.xml",
        "views/account_account_views.xml",
        "views/account_bank_statement_line_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bank_statement_import_custom/static/src/js/basic_interceptor.js",
            "bank_statement_import_custom/static/src/js/simple_interceptor.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "test": [
        "tests/test_dynamic_accounts.py",
    ],
}