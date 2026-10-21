# -*- coding: utf-8 -*-
import csv
import io
import json

import xlsxwriter

from odoo.http import Controller, request, route, content_disposition


class StockAtDateExportController(Controller):
    """Exporta o relatório Inventário a uma Data em PDF/CSV/XLSX."""

    @route('/stock_at_date/export/', type='http', auth='user')
    def export_stock_at_date(self, report_data, export_format='pdf'):
        json_data = json.loads(report_data)
        report = request.env['report.mh_stock_at_date.report']._get_report_data(json_data)

        date_obj = report.get('target_date')
        date_str = date_obj.strftime('%d-%m-%Y') if date_obj else ''
        company_name = request.env.company.name or 'Empresa'
        filename = f'{company_name} - Inventário a Data {date_str}'

        if export_format == 'pdf':
            return self._generate_pdf(filename, json_data)
        if export_format == 'csv':
            return self._generate_csv(filename, report)
        return self._generate_xlsx(filename, report)

    # ───────────────── PDF ─────────────────
    def _generate_pdf(self, filename, json_data):
        pdf, _ct = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'mh_stock_at_date.action_report_stock_at_date_pdf',
            res_ids=[request.env.company.id],
            data=json_data,
        )
        return request.make_response(pdf, [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', content_disposition(f'{filename}.pdf')),
        ])

    # ───────────────── Helpers ─────────────────
    def _build_rows(self, report):
        """Devolve linhas planas: (location, product, lot, qty, uom)."""
        rows = []
        for g in report.get('groups', []):
            loc_name = g['location'].complete_name if g['location'] else ''
            for psub in g['products']:
                prod = psub['product']
                pname = prod.display_name if prod else ''
                uom = prod.uom_id.name if prod and prod.uom_id else ''
                has_lots = any(li['lot'] for li in psub['lots'])
                if has_lots:
                    for lot_item in psub['lots']:
                        lot_name = lot_item['lot'].name if lot_item['lot'] else ''
                        rows.append([loc_name, pname, lot_name, lot_item['qty'], uom])
                else:
                    rows.append([loc_name, pname, '', psub['total_qty'], uom])
        return rows

    # ───────────────── CSV ─────────────────
    def _generate_csv(self, filename, report):
        qty_precision = report.get('qty_precision', 4)
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow(['Inventário a uma Data'])
        writer.writerow(['Empresa:', report['company'].name])
        target_date = report.get('target_date')
        date_str = target_date.strftime('%d/%m/%Y %H:%M') if target_date else ''
        writer.writerow(['À data:', date_str])
        if report.get('filter_location'):
            writer.writerow(['Localização:', report['filter_location'].complete_name])
        if report.get('filter_product'):
            writer.writerow(['Produto:', report['filter_product'].display_name])
        if report.get('filter_lot'):
            writer.writerow(['S/N:', report['filter_lot'].name])
        if report.get('classification_label'):
            writer.writerow(['Classificação:', report['classification_label']])
        writer.writerow([])
        writer.writerow(['Localização', 'Produto', 'S/N', 'Quantidade', 'UoM'])
        qty_fmt = f'{{:.{qty_precision}f}}'
        for r in self._build_rows(report):
            writer.writerow([r[0], r[1], r[2], qty_fmt.format(r[3]), r[4]])
        writer.writerow([])
        writer.writerow(['TOTAL GERAL', '', '', qty_fmt.format(report.get('grand_total', 0)), ''])
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Disposition', content_disposition(f'{filename}.csv')),
        ])

    # ───────────────── XLSX ─────────────────
    def _generate_xlsx(self, filename, report):
        qty_precision = report.get('qty_precision', 4)
        qty_fmt_str = '#,##0' + ('.' + '0' * qty_precision if qty_precision > 0 else '')

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        ws = workbook.add_worksheet('Inventário')
        ws.set_default_row(18)

        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
        })
        fmt_meta_label = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'right',
            'bg_color': '#F2F2F2', 'border': 1, 'border_color': '#DCDCDC',
        })
        fmt_meta_value = workbook.add_format({
            'font_size': 10, 'align': 'left',
            'bg_color': '#FAFAFA', 'border': 1, 'border_color': '#DCDCDC',
        })
        fmt_header = workbook.add_format({
            'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#F8F8FF', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_text = workbook.add_format({
            'font_size': 10, 'align': 'left', 'border': 1, 'border_color': '#DED9D9',
        })
        fmt_qty = workbook.add_format({
            'font_size': 10, 'align': 'right', 'num_format': qty_fmt_str,
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

        # Larguras
        ws.set_column('A:A', 30)
        ws.set_column('B:B', 50)
        ws.set_column('C:C', 30)
        ws.set_column('D:D', 15)
        ws.set_column('E:E', 10)

        row = 0
        ws.merge_range(row, 0, row, 4, 'Inventário a uma Data', fmt_title)
        row += 2

        target_date = report.get('target_date')
        date_str = target_date.strftime('%d/%m/%Y %H:%M') if target_date else ''
        meta_pairs = [
            ('Empresa:', report['company'].name),
            ('À data:', date_str),
        ]
        if report.get('filter_location'):
            meta_pairs.append(('Localização:', report['filter_location'].complete_name))
        if report.get('filter_product'):
            meta_pairs.append(('Produto:', report['filter_product'].display_name))
        if report.get('filter_lot'):
            meta_pairs.append(('S/N:', report['filter_lot'].name))
        if report.get('classification_label'):
            meta_pairs.append(('Classificação:', report['classification_label']))

        for label, value in meta_pairs:
            ws.write(row, 0, label, fmt_meta_label)
            ws.merge_range(row, 1, row, 4, value or '', fmt_meta_value)
            row += 1
        row += 1

        # Cabeçalho
        for c, h in enumerate(['Localização', 'Produto', 'S/N', 'Quantidade', 'UoM']):
            ws.write(row, c, h, fmt_header)
        row += 1

        for r in self._build_rows(report):
            ws.write(row, 0, r[0], fmt_text)
            ws.write(row, 1, r[1], fmt_text)
            ws.write(row, 2, r[2], fmt_text)
            ws.write(row, 3, r[3], fmt_qty)
            ws.write(row, 4, r[4], fmt_text)
            row += 1

        # Total
        ws.merge_range(row, 0, row, 2, 'TOTAL GERAL', fmt_total_text)
        ws.write(row, 3, report.get('grand_total', 0), fmt_total_qty)
        ws.write(row, 4, '', fmt_total_empty)

        workbook.close()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(f'{filename}.xlsx')),
        ])
