# -*- coding: utf-8 -*-
import csv
import io
import json

import xlsxwriter

from odoo.http import Controller, request, route, content_disposition


class SaftExportController(Controller):
    """Export do mapa Vendas AT (MZ): XLSX/CSV (formato PHC) e XML (SAF-T PALOP)."""

    @route('/mh_saft/export', type='http', auth='user')
    def export(self, report_data, export_format='xlsx', **kw):
        data = json.loads(report_data or '{}')
        report = request.env['report.mh_saft.report']
        company = (request.env.company.name or 'Empresa').replace(' ', '_')
        year = data.get('year') or ''
        try:
            month = f"{int(data.get('month')):02d}"
        except (TypeError, ValueError):
            month = ''
        base = f'Vendas_AT_{company}_{year}-{month}'

        if export_format == 'xml':
            xml_bytes = report.generate_saft_xml(data)
            return request.make_response(xml_bytes, [
                ('Content-Type', 'application/xml; charset=utf-8'),
                ('Content-Length', len(xml_bytes)),
                ('Content-Disposition', content_disposition(f'{base}.xml')),
            ])

        exp = report.get_export_rows(data)
        if export_format == 'csv':
            return self._csv(base, exp)
        return self._xlsx(base, exp)

    # ───────────────── CSV ─────────────────
    def _csv(self, base, exp):
        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow(exp['columns'])
        for row in exp['rows']:
            writer.writerow(row)
        content = buffer.getvalue().encode('utf-8-sig')  # BOM p/ Excel ler acentos
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'text/csv; charset=utf-8'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(f'{base}.csv')),
        ])

    # ───────────────── XLSX ─────────────────
    def _xlsx(self, base, exp):
        buffer = io.BytesIO()
        wb = xlsxwriter.Workbook(buffer, {'in_memory': True})
        ws = wb.add_worksheet('Vendas AT')

        fmt_header = wb.add_format({
            'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#F2F2F2', 'border': 1, 'border_color': '#DCDCDC',
        })
        fmt_text = wb.add_format({'font_size': 10, 'border': 1, 'border_color': '#E6E6E6'})
        fmt_num = wb.add_format({
            'font_size': 10, 'num_format': '#,##0.00', 'border': 1, 'border_color': '#E6E6E6',
        })
        # colunas numéricas (índices): preço, total_linha, iva, total_ilíquido, valor_iva, total
        num_cols = {6, 7, 8, 9, 10, 11}
        widths = [11, 12, 10, 14, 30, 40, 13, 13, 8, 15, 13, 14]
        for c, w in enumerate(widths):
            ws.set_column(c, c, w)

        for c, h in enumerate(exp['columns']):
            ws.write(0, c, h, fmt_header)
        for i, row in enumerate(exp['rows'], start=1):
            for c, val in enumerate(row):
                if c in num_cols and isinstance(val, (int, float)):
                    ws.write_number(i, c, val, fmt_num)
                else:
                    ws.write(i, c, val if val is not None else '', fmt_text)
        ws.freeze_panes(1, 0)

        # Proteger a folha (só-leitura): células bloqueadas, mas visíveis/copiáveis.
        # Sem password → pode ser desprotegida em Rever › Desproteger; para exigir
        # password, passar ws.protect('a_password', {...}).
        ws.protect('', {
            'select_locked_cells': True,
            'select_unlocked_cells': True,
            'sort': False,
            'autofilter': False,
            'format_cells': False,
        })

        wb.close()
        content = buffer.getvalue()
        buffer.close()
        return request.make_response(content, [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(f'{base}.xlsx')),
        ])
