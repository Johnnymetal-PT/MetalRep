# -*- coding: utf-8 -*-
"""Mapa "Vendas AT" / SAF-T (MZ) — facturação.

Reproduz a listagem plana que a AT de Moçambique aceita (linha a linha), no
formato do PHC "Vendas AT": Data · Documento (série=journal.code) · Número ·
Nuit · Nome · Designação · Preço unitário · Total linha · IVA · Total ilíquido
· Valor IVA · Total.

Mapa interactivo (à imagem do mh_stock_at_date) + export Excel/CSV.
O XML SAF-T (modelo PALOP) fica em `generate_saft_xml` para o SAF-T completo
(fase futura, pendente do XSD oficial + certificação/Hash ATM).
"""
from datetime import date, timedelta
import xml.etree.ElementTree as ET

from odoo import api, fields, models

INVOICE_TYPES = {'out_invoice': 'FT', 'out_refund': 'NC'}
MONTHS_PT = [
    (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
    (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
    (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro'),
]
MONTHS_ABBR_PT = ['', 'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
                  'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
# Cabeçalhos exactos do ficheiro PHC "Vendas AT"
COLUMNS = ['data', 'documento', 'número', 'nuit', 'nome_do_cliente',
           'designação', 'preço_unitário', 'total_linha', 'iva',
           'total_ilíquido', 'valor_iva', 'total']
SAFT_VERSION = '1.01_01'  # placeholder — ajustar à versão oficial da AT (MZ)


class SaftReport(models.AbstractModel):
    _name = 'report.mh_saft.report'
    _description = 'Mapa Vendas AT / SAF-T (MZ)'

    # ────────────────────── Filtros ──────────────────────
    @api.model
    def get_filters(self):
        self.env.cr.execute("""
            SELECT DISTINCT EXTRACT(YEAR FROM invoice_date)::int AS y
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund')
              AND state = 'posted' AND invoice_date IS NOT NULL
            ORDER BY y DESC
        """)
        years = [r[0] for r in self.env.cr.fetchall()]
        today = fields.Date.context_today(self)
        if not years:
            years = [today.year]
        return {
            'years': years,
            'months': [{'value': v, 'label': l} for v, l in MONTHS_PT],
            'current_year': today.year if today.year in years else years[0],
            'current_month': today.month,
        }

    # ────────────────────── Selecção de facturas ──────────────────────
    def _has_debit_note(self):
        return 'debit_origin_id' in self.env['account.move']._fields

    def _saft_type(self, inv):
        """Tipo SAF-T do documento: FT (factura), NC (nota de crédito),
        ND (nota de débito = out_invoice com debit_origin_id, via
        account_debit_note)."""
        if inv.move_type == 'out_refund':
            return 'NC'
        if self._has_debit_note() and getattr(inv, 'debit_origin_id', False):
            return 'ND'
        return 'FT'

    def _get_invoices(self, data):
        year = int(data.get('year') or fields.Date.context_today(self).year)
        month = int(data.get('month') or fields.Date.context_today(self).month)
        date_from = date(year, month, 1)
        date_to = date(year + (month // 12), (month % 12) + 1, 1)
        domain = [
            ('move_type', 'in', ['out_invoice', 'out_refund']),
            ('state', '=', 'posted'),
            ('invoice_date', '>=', date_from),
            ('invoice_date', '<', date_to),
            ('company_id', '=', self.env.company.id),
        ]
        dt = data.get('doc_type')
        has_debit = self._has_debit_note()
        if dt == 'NC':
            domain.append(('move_type', '=', 'out_refund'))
        elif dt == 'ND' and has_debit:
            domain += [('move_type', '=', 'out_invoice'), ('debit_origin_id', '!=', False)]
        elif dt == 'FT':
            domain.append(('move_type', '=', 'out_invoice'))
            if has_debit:
                domain.append(('debit_origin_id', '=', False))
        # Ordem: data, série (diário), número — como o PHC
        return self.env['account.move'].search(
            domain, order='invoice_date, journal_id, sequence_number, name')

    @api.model
    def _fmt_date(self, d):
        return f'{d.day:02d}-{MONTHS_ABBR_PT[d.month]}-{str(d.year)[-2:]}' if d else ''

    @api.model
    def _line_iva(self, line):
        """Taxa de IVA (%) da linha — primeira tax do tipo percentagem."""
        tax = line.tax_ids[:1]
        return tax.amount if tax else 0.0

    @api.model
    def _doc_series(self, inv):
        """Série do documento = código alfabético do prefixo da sequência, sem
        o ano (ex.: 'FT/2026/' → 'FT'; 'RFT/2026/' → 'RFT'). Distingue facturas
        de notas de crédito, ao contrário do journal.code (que é igual p/ ambas).
        """
        prefix = inv.sequence_prefix or ''
        code = prefix.split('/')[0].strip()
        return code or (inv.journal_id.code or '')

    # ────────────────────── Linhas planas (o coração) ──────────────────────
    def _get_rows(self, data):
        """Uma linha por LINHA de factura, no formato PHC 'Vendas AT'."""
        rows = []
        for inv in self._get_invoices(data):
            for line in inv.invoice_line_ids.filtered(
                    lambda l: l.display_type == 'product'):
                rows.append({
                    'move_id': inv.id,
                    'data': self._fmt_date(inv.invoice_date),
                    'documento': self._doc_series(inv),
                    'numero': inv.sequence_number or inv.name,
                    'nuit': inv.partner_id.vat or '',
                    'nome': inv.partner_id.name or '',
                    'designacao': line.name or line.product_id.name or '',
                    'preco_unitario': line.price_unit,
                    'total_linha': line.price_subtotal,
                    'iva': self._line_iva(line),
                    'total_iliquido': inv.amount_untaxed,
                    'valor_iva': inv.amount_tax,
                    'total': inv.amount_total,
                })
        return rows

    # ────────────────────── Dados do mapa ──────────────────────
    def _get_report_data(self, data):
        rows = self._get_rows(data)
        # totais (por documento único, para não somar totais repetidos)
        seen, doc_net, doc_iva, doc_total = set(), 0.0, 0.0, 0.0
        for r in rows:
            if r['move_id'] not in seen:
                seen.add(r['move_id'])
                doc_net += r['total_iliquido']
                doc_iva += r['valor_iva']
                doc_total += r['total']
        return {
            'company': self.env.company,
            'year': int(data.get('year') or fields.Date.context_today(self).year),
            'month': int(data.get('month') or fields.Date.context_today(self).month),
            'rows': rows,
            'n_lines': len(rows),
            'n_docs': len(seen),
            'doc_net': doc_net,
            'doc_iva': doc_iva,
            'doc_total': doc_total,
        }

    @api.model
    def get_html(self, data):
        values = self._get_report_data(data or {})
        html = self.env['ir.qweb']._render('mh_saft.report_saft_page', values)
        return {
            'html': html,
            'total_lines': values['n_lines'],
            'total_docs': values['n_docs'],
            'grand_total': values['doc_total'],
        }

    # ────────────────────── Export (linhas para CSV/XLSX) ──────────────────────
    @api.model
    def get_export_rows(self, data):
        """Devolve (cabeçalhos, linhas) no formato PHC 'Vendas AT'."""
        rows = self._get_rows(data or {})
        out = []
        for r in rows:
            out.append([
                r['data'], r['documento'], r['numero'], r['nuit'], r['nome'],
                r['designacao'], r['preco_unitario'], r['total_linha'], r['iva'],
                r['total_iliquido'], r['valor_iva'], r['total'],
            ])
        return {'columns': COLUMNS, 'rows': out}

    # ────────────────────── XML SAF-T (PALOP) — fase futura ──────────────────────
    @api.model
    def generate_saft_xml(self, data):
        """SAF-T (MZ) modelo PALOP — SalesInvoices. Reservado para o SAF-T
        completo (pendente do XSD oficial e da assinatura/Hash + certificação)."""
        invoices = self._get_invoices(data)
        company = self.env.company
        year = int(data.get('year') or fields.Date.context_today(self).year)
        month = int(data.get('month') or fields.Date.context_today(self).month)
        date_from = date(year, month, 1)
        date_to = date(year + (month // 12), (month % 12) + 1, 1)

        root = ET.Element('AuditFile')
        h = ET.SubElement(root, 'Header')
        ET.SubElement(h, 'AuditFileVersion').text = SAFT_VERSION
        ET.SubElement(h, 'CompanyID').text = company.company_registry or (company.vat or '')
        ET.SubElement(h, 'TaxRegistrationNumber').text = (company.vat or '').replace(' ', '')
        ET.SubElement(h, 'TaxAccountingBasis').text = 'F'
        ET.SubElement(h, 'CompanyName').text = company.name or ''
        ET.SubElement(h, 'FiscalYear').text = str(year)
        ET.SubElement(h, 'StartDate').text = date_from.isoformat()
        ET.SubElement(h, 'EndDate').text = (date_to - timedelta(days=1)).isoformat()
        ET.SubElement(h, 'CurrencyCode').text = company.currency_id.name or 'MZN'
        ET.SubElement(h, 'DateCreated').text = fields.Date.context_today(self).isoformat()
        ET.SubElement(h, 'ProductID').text = 'mh_saft/MakeItHappen'
        ET.SubElement(h, 'ProductVersion').text = '18.0.1.0.0'

        sd = ET.SubElement(root, 'SourceDocuments')
        si = ET.SubElement(sd, 'SalesInvoices')
        ET.SubElement(si, 'NumberOfEntries').text = str(len(invoices))
        for inv in invoices:
            node = ET.SubElement(si, 'Invoice')
            ET.SubElement(node, 'InvoiceNo').text = inv.name or ''
            ET.SubElement(node, 'InvoiceDate').text = (inv.invoice_date or date.today()).isoformat()
            ET.SubElement(node, 'InvoiceType').text = self._saft_type(inv)
            ET.SubElement(node, 'CustomerTaxID').text = inv.partner_id.vat or ''
            ET.SubElement(node, 'CustomerName').text = inv.partner_id.name or ''
            line_no = 0
            for ln in inv.invoice_line_ids.filtered(lambda l: l.display_type == 'product'):
                line_no += 1
                lnode = ET.SubElement(node, 'Line')
                ET.SubElement(lnode, 'LineNumber').text = str(line_no)
                ET.SubElement(lnode, 'ProductDescription').text = (ln.name or '')[:200]
                ET.SubElement(lnode, 'Quantity').text = f'{ln.quantity:.4f}'
                ET.SubElement(lnode, 'UnitPrice').text = f'{ln.price_unit:.4f}'
                amt = 'DebitAmount' if inv.move_type == 'out_refund' else 'CreditAmount'
                ET.SubElement(lnode, amt).text = f'{ln.price_subtotal:.2f}'
                ET.SubElement(lnode, 'TaxPercentage').text = f'{self._line_iva(ln):.2f}'
            dt = ET.SubElement(node, 'DocumentTotals')
            ET.SubElement(dt, 'TaxPayable').text = f'{inv.amount_tax:.2f}'
            ET.SubElement(dt, 'NetTotal').text = f'{inv.amount_untaxed:.2f}'
            ET.SubElement(dt, 'GrossTotal').text = f'{inv.amount_total:.2f}'
        ET.indent(root, space='  ')
        return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='UTF-8', xml_declaration=False)
