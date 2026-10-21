import csv
import io
import json
from datetime import datetime

import xlsxwriter

from odoo import _
from odoo.http import Controller, request, route, content_disposition


class StockValuationExportController(Controller):
    """Exporta o relatório de Valorização de Inventário em CSV/XLSX."""

    @route('/stock_valuation/export/', type='http', auth='user')
    def export_stock_valuation(self, report_data, export_format):
        json_data = json.loads(report_data)
        report = request.env['report.mh_stone_reports.report_stock_valuation']._get_report_data(json_data)

        meta = self._build_meta(report)
        rows = self._build_rows(report)
        totals = self._build_totals(report)
        qty_precision = report.get('qty_precision', 4)

        date_str = meta['date_str']
        company_name = meta['company_name'] or 'Empresa'
        filename = f'{company_name} - Valorização Inventário {date_str}'

        if export_format == 'pdf':
            return self._generate_pdf(filename, json_data)
        if export_format == 'csv':
            return self._generate_csv(filename, meta, rows, totals, qty_precision)
        return self._generate_xlsx(filename, meta, rows, totals, report.get('currency'), qty_precision)

    def _generate_pdf(self, filename, json_data):
        pdf, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'mh_stone_reports.action_report_stock_valuation',
            res_ids=[request.env.company.id],
            data=json_data,
        )
        return request.make_response(pdf, [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(f'{filename}.pdf')),
        ])

    # ───────────────── Helpers ─────────────────

    def _build_meta(self, report):
        company = report.get('company')
        product = report.get('product')
        classification_label = report.get('classification_label') or ''
        report_date = report.get('report_date')
        date = report.get('date')
        return {
            'title': report.get('title') or 'Valorização de Inventário',
            'company_name': company.name if company else '',
            'processed_at': report_date.strftime('%d/%m/%Y %H:%M') if report_date else '',
            'date_str': date.strftime('%d-%m-%Y') if date else '',
            'date_human': date.strftime('%d/%m/%Y') if date else '',
            'product_label': product.display_name if product else 'Todos',
            'classification_label': classification_label or 'Todas',
        }

    def _build_rows(self, report):
        """Uma linha por produto (alinhado com PDF). Valores já calculados no modelo."""
        rows = []
        for g in report.get('groups', []):
            rows.append([
                g['product_name'],
                g['total_qty'],
                g['uom'],
                g['total_value'],
            ])
        return rows

    def _build_totals(self, report):
        return [
            'TOTAL GERAL',
            report.get('grand_total_qty', 0.0),
            '',
            report.get('grand_total_value', 0.0),
        ]

    # ───────────────── CSV ─────────────────

    def _generate_csv(self, filename, meta, rows, totals, qty_precision=4):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow([meta['title']])
        writer.writerow(['Empresa:', meta['company_name']])
        writer.writerow(['Processado em:', meta['processed_at']])
        writer.writerow([])
        writer.writerow(['Data de Valorização:', meta['date_human']])
        writer.writerow(['Artigo:', meta['product_label']])
        writer.writerow(['Classificação:', meta['classification_label']])
        writer.writerow([])
        writer.writerow([
            _('Produto'),
            _('Quantidade'),
            _('UoM'),
            _('Valor'),
        ])
        qty_fmt = f'{{:.{qty_precision}f}}'
        for r in rows:
            writer.writerow([
                r[0],
                qty_fmt.format(r[1]),
                r[2],
                f'{r[3]:.2f}',
            ])
        writer.writerow([
            totals[0],
            qty_fmt.format(totals[1]),
            '',
            f'{totals[3]:.2f}',
        ])
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', content_disposition(f'{filename}.csv')),
        ])

    # ───────────────── XLSX ─────────────────

    def _generate_xlsx(self, filename, meta, rows, totals, currency, qty_precision=4):
        currency_symbol = currency.symbol if currency else ''
        currency_pos = currency.position if currency else 'after'

        money_fmt_str = (
            f'#,##0.00 "{currency_symbol}"' if currency_pos == 'after'
            else f'"{currency_symbol}" #,##0.00'
        )
        qty_fmt_str = '#,##0' + ('.' + '0' * qty_precision if qty_precision > 0 else '')

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet('Valorização')
        worksheet.set_default_row(18)

        # Formatos
        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter',
        })
        fmt_meta_label = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'right', 'bg_color': '#F2F2F2',
            'border': 1, 'border_color': '#DCDCDC',
        })
        fmt_meta_value = workbook.add_format({
            'font_size': 10, 'align': 'left', 'bg_color': '#FAFAFA',
            'border': 1, 'border_color': '#DCDCDC',
        })
        fmt_header = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#F8F8FF', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_text = workbook.add_format({
            'font_size': 10, 'align': 'left', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_center = workbook.add_format({
            'font_size': 10, 'align': 'center', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_qty = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': qty_fmt_str,
            'border': 1, 'border_color': '#DED9D9',
        })
        fmt_money = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': money_fmt_str,
            'border': 1, 'border_color': '#DED9D9',
        })
        fmt_total_text = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'left', 'bg_color': '#E0E0E0',
            'border': 1, 'border_color': '#DED9D9',
        })
        fmt_total_qty = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'right', 'num_format': qty_fmt_str,
            'bg_color': '#E0E0E0', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_total_empty = workbook.add_format({
            'bg_color': '#E0E0E0', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_total_money = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'right', 'num_format': money_fmt_str,
            'bg_color': '#E0E0E0', 'border': 1, 'border_color': '#DED9D9',
        })

        # Título
        worksheet.merge_range('A1:D1', meta['title'], fmt_title)
        worksheet.set_row(0, 28)

        # Bloco de metadados (linhas 2-7, A:B + C:D)
        meta_rows = [
            ('Empresa:', meta['company_name'], 'Data de Valorização:', meta['date_human']),
            ('Processado em:', meta['processed_at'], 'Artigo:', meta['product_label']),
            ('', '', 'Classificação:', meta['classification_label']),
        ]
        for i, (l1, v1, l2, v2) in enumerate(meta_rows, start=2):
            if l1:
                worksheet.write(f'A{i}', l1, fmt_meta_label)
                worksheet.write(f'B{i}', v1, fmt_meta_value)
            worksheet.write(f'C{i}', l2, fmt_meta_label)
            worksheet.write(f'D{i}', v2, fmt_meta_value)

        # Cabeçalho da tabela (linha 6)
        header_row = 5  # 0-indexed → linha 6 no Excel
        headers = ['Produto', 'Quantidade', 'UoM', 'Valor']
        for col, h in enumerate(headers):
            worksheet.write(header_row, col, h, fmt_header)
        worksheet.set_row(header_row, 22)

        # Dados
        data_start = header_row + 1
        column_widths = [len(h) for h in headers]
        for row_idx, r in enumerate(rows, start=data_start):
            worksheet.write(row_idx, 0, r[0], fmt_text)
            worksheet.write_number(row_idx, 1, float(r[1]), fmt_qty)
            worksheet.write(row_idx, 2, r[2], fmt_center)
            worksheet.write_number(row_idx, 3, float(r[3]), fmt_money)
            cells = [r[0], f'{r[1]:,.{qty_precision}f}', r[2], f'{r[3]:,.2f}']
            for col_idx, cell in enumerate(cells):
                column_widths[col_idx] = max(column_widths[col_idx], len(str(cell)))

        # Total geral
        total_row = data_start + len(rows)
        worksheet.write(total_row, 0, totals[0], fmt_total_text)
        worksheet.write_number(total_row, 1, float(totals[1]), fmt_total_qty)
        worksheet.write(total_row, 2, '', fmt_total_empty)
        worksheet.write_number(total_row, 3, float(totals[3]), fmt_total_money)

        # Larguras
        for col_idx, w in enumerate(column_widths):
            worksheet.set_column(col_idx, col_idx, max(w + 3, 12))
        worksheet.set_column(0, 0, max(column_widths[0] + 3, 40))  # Produto mais larga

        # Freeze pane no cabeçalho da tabela
        worksheet.freeze_panes(header_row + 1, 0)

        workbook.close()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(f'{filename}.xlsx')),
        ])
