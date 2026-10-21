"""Customizacoes visuais do Partner Ledger e Aged Receivable.

Duas alteracoes principais aos relatorios standard Enterprise:
1. Limpa o ``name`` (parte ate ao primeiro ``\\n`` / ``( `` / ``/ ``)
   para evitar nomes multi-linha que partem o layout em PDF.
2. Acrescenta classe CSS ``partner-header partner-header-pdf`` para
   alinhar a celula com o estilo definido em
   ``static/src/css/account_report_pdf.css``.
"""
from odoo import models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CustomPartnerLedgerReport(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift=0):
        # caret_type controla o tipo de detalhe a abrir no relatorio
        # (payment vs move line).
        if aml_query_result['payment_id']:
            caret_type = 'account.payment'
        else:
            caret_type = 'account.move.line'

        columns = []
        report = self.env['account.report'].browse(options['report_id'])

        # Constroi celulas com tratamento especial para balance (soma
        # do saldo inicial) e amount_currency (esconde quando == moeda da company).
        for column in options['columns']:
            col_expr_label = column['expression_label']
            if col_expr_label not in aml_query_result:
                raise UserError(_("The column '%s' is not available for this report." % col_expr_label))

            col_value = aml_query_result[col_expr_label] if column['column_group_key'] == aml_query_result['column_group_key'] else None

            if col_value is None:
                columns.append(report._build_column_dict(None, None))
            else:
                currency = False
                if col_expr_label == 'balance':
                    # Saldo acumulado: somar saldo inicial do periodo.
                    col_value += init_bal_by_col_group[column['column_group_key']]
                if col_expr_label == 'amount_currency':
                    currency = self.env['res.currency'].browse(aml_query_result['currency_id'])
                    if currency == self.env.company.currency_id:
                        # Mesma moeda da company - omitir para nao
                        # poluir o relatorio com EUR repetido.
                        col_value = ''
                columns.append(report._build_column_dict(col_value, column, options=options, currency=currency))

        return {
            'id': report._get_generic_line_id('account.move.line', aml_query_result['id'], parent_line_id=partner_line_id, markup=aml_query_result['partial_id']),
            'parent_id': partner_line_id,
            'name': aml_query_result['name'],
            'columns': columns,
            'caret_options': caret_type,
            'level': 3 + level_shift,
            'class': 'partner-header partner-header-pdf',
        }

    def get_report_information(self, options):
        info = super().get_report_information(options)
        # Substitui o tbody do PDF pelo template custom para aplicar
        # a classe partner-header com estilo da Piccolo.
        info.setdefault('custom_display', {}).setdefault('pdf_export', {})
        info['custom_display']['pdf_export'].update({
            'pdf_export_main_table_body': 'pg_bd_connection.pdf_export_main_table_body_inherit',
        })
        return info


class CustomAgedReceivableReport(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    def _report_custom_engine_aged_receivable(self, expressions, options, date_scope, current_groupby, next_groupby, offset=0, limit=None, warnings=None):
        results = super()._report_custom_engine_aged_receivable(
            expressions, options, date_scope, current_groupby, next_groupby, offset, limit, warnings,
        )

        # Limpa nomes multi-linha: usa apenas a primeira linha e descarta
        # o que vem a seguir a um " / " (sufixos como "S00120 / Hotel XYZ").
        for record in results:
            if isinstance(record, tuple):
                record_data = record[1]
                if 'name' in record_data:
                    record_data['name'] = record_data['name'].split("\n")[0].split(" / ")[0]
            elif isinstance(record, dict):
                if 'name' in record:
                    record['name'] = record['name'].split("\n")[0].split(" / ")[0]
        return results

    def _custom_line_postprocessor(self, report, options, lines, warnings=None):
        # Mesma higienizacao do name + classe CSS para o partner header
        # ficar consistente com o estilo PDF da Piccolo.
        for line in lines:
            if isinstance(line, dict) and 'name' in line:
                original_name = line['name']
                cleaned_name = original_name.split("\n")[0].split(" (")[0].split(" / ")[0]
                line['name'] = cleaned_name
                if line.get("level") == 2:
                    line.setdefault('class', '')
                    line['class'] += ' partner-header partner-header-pdf'
        return lines
