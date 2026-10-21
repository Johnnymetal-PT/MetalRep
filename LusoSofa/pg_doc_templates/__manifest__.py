{
    "name": "PG Doc Templates",
    "version": "19.0.1.5.0",
    "category": "Knowledge",
    "summary": "Markdown raw templates source-of-truth para PG Framework",
    "author": "Parametro",
    "depends": ["knowledge"],
    "data": [
        "security/ir.model.access.csv",
        "security/pg_doc_templates_security.xml",
        "views/pg_template_settings_wizard_views.xml",
        "views/knowledge_article_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
    "post_init_hook": "post_init_hook",
}
