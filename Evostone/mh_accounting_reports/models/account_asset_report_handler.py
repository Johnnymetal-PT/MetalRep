from odoo import _, models


class AssetsReportCustomHandler(models.AbstractModel):
    _inherit = 'account.asset.report.handler'

    def _custom_options_initializer(self, report, options, previous_options):
        """Override subheaders para usar terminologia oficial MZ (Dec. 72/2013)
        e acomodar a nova coluna Taxa %."""
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        options['custom_columns_subheaders'] = [
            {"name": _("Características"), "colspan": 4},
            {"name": _("Valores de Aquisição"), "colspan": 4},
            {"name": _("Reintegrações e Amortizações"), "colspan": 4},
            {"name": _("Activo Imobilizado"), "colspan": 1},
            {"name": _("Taxa"), "colspan": 1},
        ]

    def _get_parent_asset_values(self, options, asset_line, asset_children_lines):
        """Adiciona taxa de depreciação % ao relatório de activos."""
        values = super()._get_parent_asset_values(options, asset_line, asset_children_lines)

        if asset_line['asset_method'] == 'linear' and asset_line['asset_method_number']:
            total_months = int(asset_line['asset_method_number']) * int(asset_line['asset_method_period'])
            total_years = total_months / 12
            rate = (100 / total_years) if total_years else 0
            values['depreciation_rate_pct'] = '{:.2f} %'.format(rate)
        elif asset_line['asset_method'] == 'linear':
            values['depreciation_rate_pct'] = '0.00 %'
        else:
            values['depreciation_rate_pct'] = '{:.2f} %'.format(
                float(asset_line['asset_method_progress_factor']) * 100
            )

        return values
