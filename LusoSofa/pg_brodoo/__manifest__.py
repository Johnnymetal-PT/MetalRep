{
    'name': 'Brodoo',
    'version': '19.0.1.14.0',
    'category': 'Services/Project',
    'summary': 'Espelho factual de projectos Odoo para repositórios GitHub com suporte a agentes AI',
    'description': """
        Espelho factual de projectos Odoo para repositórios GitHub:
        - Publica o espelho (mirror) do projecto de Odoo para GitHub
        - Publica snapshots factuais de âmbito (scope) do projecto
        - Publica snapshots factuais de esforço (effort) do projecto
        - Onboarding de projectos e ligação a repositórios GitHub
    """,
    'author': 'Parametro',
    'depends': ['project'],
    'assets': {
        'web.assets_backend': [
            'pg_brodoo/static/src/scss/pg_brodoo.scss',
        ],
        'web.assets_web_dark': [
            'pg_brodoo/static/src/scss/pg_brodoo.dark.scss',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/pg_mirror_sync_cron.xml',
        'data/pg_scope_sync_cron.xml',
        'views/pg_ai_repository_views.xml',
        'views/pg_ai_onboarding_wizard_views.xml',
        'views/pg_project_batch_onboarding_wizard_views.xml',
        'views/pg_project_batch_rebuild_artifacts_wizard_views.xml',
        'views/pg_branch_create_wizard_views.xml',
        'views/pg_project_scope_sync_run_views.xml',
        'views/pg_project_effort_sync_run_views.xml',
        'views/pg_project_mirror_sync_run_views.xml',
        'views/project_project_views.xml',
        'views/project_task_scope_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'OPL-1',
}
