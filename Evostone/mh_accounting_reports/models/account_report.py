from odoo import fields, models


class AccountReport(models.Model):
    _inherit = 'account.report'

    def get_default_report_filename(self, options, extension):
        """Customizar nome do ficheiro para o Mapa de Cobranças:
        - 1 cliente: "Mapa de Cobranças - NomeCliente"
        - Vários/todos: "Mapa de Cobranças - YYYY-MM-DD"
        """
        self.ensure_one()

        collection_map = self.env.ref(
            'mh_accounting_reports.aged_customer_invoices_report',
            raise_if_not_found=False,
        )
        payment_map = self.env.ref(
            'mh_accounting_reports.aged_supplier_invoices_report',
            raise_if_not_found=False,
        )
        report_label = None
        if collection_map and self == collection_map:
            report_label = 'Mapa de Cobranças'
        elif payment_map and self == payment_map:
            report_label = 'Mapa de Pagamentos'

        if report_label:
            partner_ids = options.get('partner_ids') or []
            if len(partner_ids) == 1:
                partner = self.env['res.partner'].browse(partner_ids[0])
                suffix = partner.name or fields.Date.context_today(self).isoformat()
            else:
                suffix = fields.Date.context_today(self).isoformat()
            # Sanitizar caracteres problemáticos em nomes de ficheiros
            safe_suffix = suffix.replace('/', '-').replace('\\', '-').strip()
            return f"{report_label} - {safe_suffix}.{extension}"

        return super().get_default_report_filename(options, extension)

    def _get_options_date_domain(self, options, date_scope):
        """SÓ no Mapa de Pagamentos: filtrar pela DATA DO DOCUMENTO
        (``move_id.invoice_date``) em vez da data contabilística (``date``).

        Motivo: uma factura de fornecedor pode ter a data do documento num mês
        (ex.: 10-08) e a data contabilística noutro (ex.: 31-08). O Aged Payable
        nativo filtra sempre pela data contabilística, pelo que a factura "some"
        de quem espera vê-la pelo mês do documento. Aqui o mapa passa a incluir
        as linhas pela data do documento.

        Movimentos SEM data de documento — pagamentos, banco/caixa, lançamentos
        manuais — não têm ``invoice_date``; para esses cai-se de volta na data
        contabilística (equivalente a ``COALESCE(invoice_date, date)``), para que
        nenhum pagamento desapareça do mapa.

        Qualquer outro relatório mantém o comportamento nativo (data contabilística).
        """
        payment_map = self.env.ref(
            'mh_accounting_reports.aged_supplier_invoices_report',
            raise_if_not_found=False,
        )
        if not payment_map or self != payment_map:
            return super()._get_options_date_domain(options, date_scope)

        date_from, date_to = self._get_date_bounds_info(options, date_scope)

        # Limite superior: COALESCE(invoice_date, date) <= date_to
        domain = [
            '|',
                '&', ('move_id.invoice_date', '!=', False), ('move_id.invoice_date', '<=', date_to),
                '&', ('move_id.invoice_date', '=', False), ('date', '<=', date_to),
        ]
        if date_from:
            # Limite inferior: COALESCE(invoice_date, date) >= date_from
            domain += [
                '|',
                    '&', ('move_id.invoice_date', '!=', False), ('move_id.invoice_date', '>=', date_from),
                    '&', ('move_id.invoice_date', '=', False), ('date', '>=', date_from),
            ]
        return domain
