"""Post-install hook to rename the Depreciation Schedule report
in all installed languages."""

NEW_NAME = 'Mapa das Reintegrações e Amortizações'

RECORDS_TO_UPDATE = [
    ('account_asset.assets_report', 'account.report'),
    ('account_asset.action_account_report_assets', 'ir.actions.client'),
    ('account_asset.menu_action_account_report_assets', 'ir.ui.menu'),
]


def post_init_hook(env):
    """Update the name in every installed language (including pt_PT)."""
    installed_langs = env['res.lang'].search([('active', '=', True)]).mapped('code')

    for xml_id, _model in RECORDS_TO_UPDATE:
        record = env.ref(xml_id, raise_if_not_found=False)
        if not record:
            continue
        for lang in installed_langs:
            record.with_context(lang=lang).name = NEW_NAME
