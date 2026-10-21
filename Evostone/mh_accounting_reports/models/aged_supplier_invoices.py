from odoo import models, fields


class AgedSupplierInvoicesHandler(models.AbstractModel):
    _name = 'account.aged.supplier.invoices.report.handler'
    _inherit = 'account.aged.partner.balance.report.handler'
    _description = 'Aged Supplier Invoices Report Handler'

    def _get_custom_display_config(self):
        config = super()._get_custom_display_config()
        config['components'] = config.get('components', {})
        config['components']['AccountReportLineCell'] = 'mh_accounting_reports.CollectionMapLineCell'
        config['pdf_export'] = config.get('pdf_export', {})
        config['pdf_export']['pdf_export_main'] = 'mh_accounting_reports.payment_map_pdf_main'
        return config

    def _report_custom_engine_aged_supplier_invoices(
        self, expressions, options, date_scope, current_groupby, next_groupby,
        offset=0, limit=None, warnings=None
    ):
        """Usa o mesmo motor do Aged Payable mas com aging_days e invoice_total."""
        result = self._aged_partner_report_custom_engine_common(
            options, 'liability_payable', current_groupby, next_groupby,
            offset=offset, limit=limit
        )

        date_to = fields.Date.from_string(options['date']['date_to'])

        if isinstance(result, dict):
            result['aging_days'] = self._calc_aging_days(result.get('due_date'), date_to)
            result['invoice_total'] = None
            result['amount_residual'] = None
            result['invoice_date'] = None
        elif isinstance(result, list):
            move_line_ids = []
            for item in result:
                if isinstance(item, tuple) and len(item) == 2:
                    key = item[0]
                    if current_groupby == 'id' and key:
                        move_line_ids.append(key)

            invoice_totals = {}
            invoice_residuals = {}
            move_types = {}
            doc_dates = {}
            if move_line_ids and current_groupby == 'id':
                self._cr.execute("""
                    SELECT aml.id, move.amount_total_signed, move.amount_residual_signed,
                           move.move_type, move.invoice_date, move.date
                    FROM account_move_line aml
                    JOIN account_move move ON move.id = aml.move_id
                    WHERE aml.id IN %s
                """, (tuple(move_line_ids),))
                for aml_id, amount_total, amount_residual, move_type, inv_date, move_date in self._cr.fetchall():
                    invoice_totals[aml_id] = abs(amount_total)
                    invoice_residuals[aml_id] = abs(amount_residual)
                    move_types[aml_id] = move_type
                    # Data do Documento: data da fatura se existir, senão data do movimento
                    doc_dates[aml_id] = inv_date or move_date

            for item in result:
                if isinstance(item, tuple) and len(item) == 2:
                    key, vals = item
                    # Data e Estado de Vencimento só fazem sentido para faturas e
                    # notas de crédito. Para pagamentos e outros lançamentos, deixar
                    # ambos em branco.
                    is_invoice = (
                        current_groupby == 'id'
                        and move_types.get(key) in ('in_invoice', 'in_refund')
                    )
                    if is_invoice:
                        vals['aging_days'] = self._calc_aging_days(vals.get('due_date'), date_to)
                    else:
                        vals['due_date'] = None
                        vals['aging_days'] = None
                    if current_groupby == 'id' and key in invoice_totals:
                        vals['invoice_total'] = invoice_totals[key]
                        vals['amount_residual'] = invoice_residuals.get(key, 0)
                    else:
                        vals['invoice_total'] = None
                        vals['amount_residual'] = None
                    # Data do Documento: preenchida para todos os movimentos
                    vals['invoice_date'] = doc_dates.get(key)

        return result

    def _calc_aging_days(self, due_date, date_to):
        if not due_date:
            return None
        if isinstance(due_date, str):
            due_date = fields.Date.from_string(due_date)
        delta = (date_to - due_date).days
        if delta < 0:
            return f"A vencer ({abs(delta)} dias)"
        elif delta == 0:
            return "Hoje"
        else:
            return f"{delta} dias em atraso"

    def _custom_options_initializer(self, report, options, previous_options):
        # Forçar mostrar moeda por defeito (fornecedores são tipicamente
        # estrangeiros — USD/EUR/ZAR). Só tem efeito se o utilizador tiver
        # o grupo Multi-Moeda; o super() lê esta flag para decidir mostrar
        # as colunas 'amount_currency' e 'currency'.
        previous_options = dict(previous_options or {})
        previous_options.setdefault('show_currency', True)

        super()._custom_options_initializer(report, options, previous_options=previous_options)
        options.setdefault('forced_domain', [])
        # NOTA: restrição desativada para o Mapa de Pagamentos incluir tudo o que o
        # Aged Payable nativo inclui na conta de fornecedores (liability_payable) com
        # remanescente por reconciliar — faturas, notas de crédito, pagamentos
        # (account.payment) e lançamentos manuais. Para voltar a mostrar apenas
        # faturas/notas de crédito, reativar as linhas abaixo.
        # options['forced_domain'] += [
        #     ('move_id.move_type', 'in', ('in_invoice', 'in_refund')),
        # ]
