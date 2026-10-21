import csv
import io
import json

import xlsxwriter

from odoo import _
from odoo.http import Controller, request, route, content_disposition


class StonePricelistExportController(Controller):
    """Exporta o relatório de Lista de Preços de Pedras em CSV/XLSX/PDF."""

    @route('/stone_stock/export/pricelist/', type='http', auth='user')
    def export_stone_pricelist(self, report_data, export_format):
        json_data = json.loads(report_data)
        report = request.env['report.mh_stone_reports.report_stone_pricelist']._get_report_data(json_data)

        meta = self._build_meta(report)
        rows = self._build_rows(report)
        filename = self._filename(meta)

        if export_format == 'pdf':
            return self._generate_pdf(filename, json_data)
        if export_format == 'csv':
            return self._generate_csv(filename, meta, rows)
        return self._generate_xlsx(filename, meta, rows, report.get('currency'))

    # ───────────────── Helpers ─────────────────

    def _build_meta(self, report):
        company = report.get('company')
        product = report.get('product')
        pricelist = report.get('pricelist')
        report_date = report.get('report_date')
        return {
            'title': report.get('title') or 'Lista de Preços',
            'company_name': company.name if company else '',
            'processed_at': report_date.strftime('%d/%m/%Y %H:%M') if report_date else '',
            'pricelist_label': pricelist.display_name if pricelist else 'Padrão',
            'product_label': product.display_name if product else 'Todos',
        }

    def _filename(self, meta):
        suffix = meta['pricelist_label'] if meta['pricelist_label'] != 'Padrão' else meta['processed_at'].split(' ')[0].replace('/', '-')
        return f'Lista de Preços - {suffix}'

    def _build_rows(self, report):
        return [
            [r['description'], r['area'], r['uom'], r['unit_price'], r['total_price']]
            for r in report.get('rows', [])
        ]

    def _generate_pdf(self, filename, json_data):
        pdf, _content_type = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'mh_stone_reports.action_report_stone_pricelist',
            res_ids=[request.env.company.id],
            data=json_data,
        )
        return request.make_response(pdf, [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(f'{filename}.pdf')),
        ])

    # ───────────────── CSV ─────────────────

    def _generate_csv(self, filename, meta, rows):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow([meta['title']])
        writer.writerow(['Empresa:', meta['company_name']])
        writer.writerow(['Processado em:', meta['processed_at']])
        writer.writerow([])
        writer.writerow(['Pricelist:', meta['pricelist_label']])
        writer.writerow(['Artigo:', meta['product_label']])
        writer.writerow([])
        writer.writerow([
            _('Descrição'),
            _('Área (m²)'),
            _('UoM'),
            _('Preço/UoM'),
            _('Preço Total'),
        ])
        for r in rows:
            writer.writerow([
                r[0],
                f'{r[1]:.4f}',
                r[2],
                f'{r[3]:.2f}',
                f'{r[4]:.2f}',
            ])
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', content_disposition(f'{filename}.csv')),
        ])

    # ───────────────── XLSX ─────────────────

    def _generate_xlsx(self, filename, meta, rows, currency):
        currency_symbol = currency.symbol if currency else ''
        currency_pos = currency.position if currency else 'after'
        money_fmt_str = (
            f'#,##0.00 "{currency_symbol}"' if currency_pos == 'after'
            else f'"{currency_symbol}" #,##0.00'
        )
        area_fmt_str = '#,##0.0000'

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet('Lista de Preços')
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
        fmt_area = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': area_fmt_str,
            'border': 1, 'border_color': '#DED9D9',
        })
        fmt_money = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': money_fmt_str,
            'border': 1, 'border_color': '#DED9D9',
        })

        # Título
        worksheet.merge_range('A1:E1', meta['title'], fmt_title)
        worksheet.set_row(0, 28)

        # Metadados
        meta_rows = [
            ('Empresa:', meta['company_name'], 'Pricelist:', meta['pricelist_label']),
            ('Processado em:', meta['processed_at'], 'Artigo:', meta['product_label']),
        ]
        for i, (l1, v1, l2, v2) in enumerate(meta_rows, start=2):
            worksheet.write(f'A{i}', l1, fmt_meta_label)
            worksheet.write(f'B{i}', v1, fmt_meta_value)
            worksheet.write(f'C{i}', l2, fmt_meta_label)
            worksheet.merge_range(f'D{i}:E{i}', v2, fmt_meta_value)

        # Cabeçalho da tabela
        header_row = 4  # 0-indexed → linha 5
        headers = ['Descrição', 'Área (m²)', 'UoM', 'Preço/UoM', 'Preço Total']
        for col, h in enumerate(headers):
            worksheet.write(header_row, col, h, fmt_header)
        worksheet.set_row(header_row, 22)

        # Dados
        data_start = header_row + 1
        column_widths = [len(h) for h in headers]
        for row_idx, r in enumerate(rows, start=data_start):
            worksheet.write(row_idx, 0, r[0], fmt_text)
            worksheet.write_number(row_idx, 1, float(r[1]), fmt_area)
            worksheet.write(row_idx, 2, r[2], fmt_center)
            worksheet.write_number(row_idx, 3, float(r[3]), fmt_money)
            worksheet.write_number(row_idx, 4, float(r[4]), fmt_money)
            cells = [r[0], f'{r[1]:,.4f}', r[2], f'{r[3]:,.2f}', f'{r[4]:,.2f}']
            for col_idx, cell in enumerate(cells):
                column_widths[col_idx] = max(column_widths[col_idx], len(str(cell)))

        # Larguras (Descrição mais larga)
        for col_idx, w in enumerate(column_widths):
            worksheet.set_column(col_idx, col_idx, max(w + 3, 12))
        worksheet.set_column(0, 0, max(column_widths[0] + 3, 50))

        # Freeze pane no cabeçalho da tabela
        worksheet.freeze_panes(header_row + 1, 0)

        workbook.close()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(f'{filename}.xlsx')),
        ])
