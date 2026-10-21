import csv
import io
import json

import xlsxwriter

from odoo import _
from odoo.http import Controller, request, route, content_disposition


class StockNoStockExportController(Controller):
    """Exporta o relatório de Artigos sem Stock em CSV/XLSX/PDF."""

    @route('/stock_no_stock/export/', type='http', auth='user')
    def export_stock_no_stock(self, report_data, export_format):
        json_data = json.loads(report_data)
        report = request.env['report.mh_stone_reports.report_stock_no_stock']._get_report_data(json_data)

        meta = self._build_meta(report)
        rows = self._build_rows(report)

        company_name = meta['company_name'] or 'Empresa'
        filename = f'{company_name} - Artigos sem Stock'

        if export_format == 'pdf':
            return self._generate_pdf(filename, json_data)
        if export_format == 'csv':
            return self._generate_csv(filename, meta, rows)
        return self._generate_xlsx(filename, meta, rows, report.get('currency'))

    def _generate_pdf(self, filename, json_data):
        pdf, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'mh_stone_reports.action_report_stock_no_stock',
            res_ids=[request.env.company.id],
            data=json_data,
        )
        return request.make_response(pdf, [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(f'{filename}.pdf')),
        ])

    def _build_meta(self, report):
        company = report.get('company')
        report_date = report.get('report_date')
        return {
            'title': report.get('title') or 'Artigos sem Stock',
            'company_name': company.name if company else '',
            'processed_at': report_date.strftime('%d/%m/%Y %H:%M') if report_date else '',
            'classification_label': report.get('classifications_label') or 'Todas',
            'supplier_label': report.get('supplier_label') or 'Todos',
            'warehouse_label': report.get('warehouse_label') or 'Todos',
        }

    def _build_rows(self, report):
        rows = []
        for g in report.get('groups', []):
            for r in g.get('rows', []):
                rows.append([
                    r['product_name'],
                    r['classification_name'],
                    r['uom'],
                    r['last_supplier_name'],
                    r['last_cost'],
                ])
        return rows

    def _generate_csv(self, filename, meta, rows):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow([meta['title']])
        writer.writerow(['Empresa:', meta['company_name']])
        writer.writerow(['Processado em:', meta['processed_at']])
        writer.writerow([])
        writer.writerow(['Classificação:', meta['classification_label']])
        writer.writerow(['Fornecedor:', meta['supplier_label']])
        writer.writerow(['Armazém:', meta['warehouse_label']])
        writer.writerow([])
        writer.writerow([
            _('Produto'),
            _('Classificação'),
            _('UoM'),
            _('Último Fornecedor'),
            _('Último Preço de Compra'),
        ])
        for r in rows:
            writer.writerow([
                r[0], r[1], r[2], r[3],
                f'{r[4]:.2f}',
            ])
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', content_disposition(f'{filename}.csv')),
        ])

    def _generate_xlsx(self, filename, meta, rows, currency):
        currency_symbol = currency.symbol if currency else ''
        currency_pos = currency.position if currency else 'after'
        money_fmt_str = (
            f'#,##0.00 "{currency_symbol}"' if currency_pos == 'after'
            else f'"{currency_symbol}" #,##0.00'
        )

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet('Sem Stock')
        worksheet.set_default_row(18)

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
        fmt_money = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': money_fmt_str,
            'border': 1, 'border_color': '#DED9D9',
        })

        worksheet.merge_range('A1:E1', meta['title'], fmt_title)
        worksheet.set_row(0, 28)

        meta_rows = [
            ('Empresa:', meta['company_name'], 'Classificação:', meta['classification_label']),
            ('Processado em:', meta['processed_at'], 'Fornecedor:', meta['supplier_label']),
            ('', '', 'Armazém:', meta['warehouse_label']),
        ]
        for i, (l1, v1, l2, v2) in enumerate(meta_rows, start=2):
            if l1:
                worksheet.write(f'A{i}', l1, fmt_meta_label)
                worksheet.write(f'B{i}', v1, fmt_meta_value)
            worksheet.write(f'C{i}', l2, fmt_meta_label)
            worksheet.merge_range(f'D{i}:E{i}', v2, fmt_meta_value)

        header_row = 5
        headers = ['Produto', 'Classificação', 'UoM', 'Último Fornecedor', 'Último Preço de Compra']
        for col, h in enumerate(headers):
            worksheet.write(header_row, col, h, fmt_header)
        worksheet.set_row(header_row, 22)

        data_start = header_row + 1
        column_widths = [len(h) for h in headers]
        for row_idx, r in enumerate(rows, start=data_start):
            worksheet.write(row_idx, 0, r[0], fmt_text)
            worksheet.write(row_idx, 1, r[1], fmt_text)
            worksheet.write(row_idx, 2, r[2], fmt_center)
            worksheet.write(row_idx, 3, r[3], fmt_text)
            worksheet.write_number(row_idx, 4, float(r[4]), fmt_money)
            cells = [r[0], r[1], r[2], r[3], f'{r[4]:,.2f}']
            for col_idx, cell in enumerate(cells):
                column_widths[col_idx] = max(column_widths[col_idx], len(str(cell)))

        for col_idx, w in enumerate(column_widths):
            worksheet.set_column(col_idx, col_idx, max(w + 3, 12))
        worksheet.set_column(0, 0, max(column_widths[0] + 3, 40))

        worksheet.freeze_panes(header_row + 1, 0)

        workbook.close()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(f'{filename}.xlsx')),
        ])
