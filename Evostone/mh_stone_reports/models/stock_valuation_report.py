from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import float_is_zero, float_round


DEFAULT_PAGE_SIZE = 80


class StockValuationReport(models.AbstractModel):
    _name = 'report.mh_stone_reports.report_stock_valuation'
    _description = 'Relatório de Valorização de Inventário à Data'

    def _get_report_values(self, docids, data):
        return self._get_report_data(data or {}, 'pdf')

    @api.model
    def get_html(self, data):
        render_values = self._get_report_data(data or {}, 'html')
        html = self.env['ir.qweb']._render(
            'mh_stone_reports.report_stock_valuation_page',
            render_values,
        )
        return {
            'html': html,
            'total_svls': render_values['total_svls'],
            'total_groups': len(render_values['groups']),
            'page_size': render_values['page_size'],
        }

    def _get_report_data(self, data, report_type='html'):
        # Relatório só-leitura, cujo acesso já está restringido pelo grupo do menu
        # (group_report_stock_valuation). sudo() para ler stock.valuation.layer e
        # modelos afins sem exigir "Inventário/Administrador".
        self = self.sudo()
        company = self.env.company

        # Precisões dinâmicas — respeitam o que estiver configurado em
        # Definições → Técnico → Precisão Decimal.
        qty_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        price_precision = self.env['decimal.precision'].precision_get('Product Price')

        date_str = data.get('date')
        if date_str:
            date = fields.Date.to_date(date_str)
        else:
            date = fields.Date.context_today(self)
        date_end = fields.Datetime.to_datetime(date).replace(hour=23, minute=59, second=59)

        product_id = data.get('product_id')
        product_id = product_id and int(product_id)
        product = (
            self.env['product.product'].browse(product_id).exists()
            if product_id else False
        )

        classification = data.get('classification') or False
        classification_label = ''
        if classification:
            sel = dict(self.env['product.template']._fields['product_classification'].selection)
            classification_label = sel.get(classification, '')

        # Filtro por lançamento contabilístico: all | with | without
        accounting_filter = data.get('accounting_filter') or 'all'
        accounting_labels = {
            'all': 'Todos',
            'with': 'Com lançamento',
            'without': 'Sem lançamento',
        }
        accounting_filter_label = accounting_labels.get(accounting_filter, 'Todos')

        page_size = int(data.get('page_size') or DEFAULT_PAGE_SIZE)

        domain = [
            ('create_date', '<=', date_end),
            ('company_id', '=', company.id),
            ('product_id.is_storable', '=', True),
        ]
        if product:
            domain.append(('product_id', '=', product.id))
        if classification:
            domain.append(('product_id.product_tmpl_id.product_classification', '=', classification))
        if accounting_filter == 'with':
            domain.append(('account_move_id', '!=', False))
        elif accounting_filter == 'without':
            domain.append(('account_move_id', '=', False))

        svls = self.env['stock.valuation.layer'].search(
            domain, order='product_id, create_date, id'
        )

        groups_map = defaultdict(list)
        for svl in svls:
            groups_map[svl.product_id.id].append(svl)

        groups = []
        raw_grand_qty = 0.0
        raw_grand_value = 0.0
        for pid, svl_list in groups_map.items():
            prod = self.env['product.product'].browse(pid)
            svl_rows = []
            total_qty = 0.0
            total_value = 0.0
            for svl in svl_list:
                svl_rows.append({
                    'id': svl.id,
                    'date': svl.create_date,
                    'reference': svl.reference or '',
                    'description': svl.description or '',
                    'lot_group_id': svl.lot_group_id.id if svl.lot_group_id else False,
                    'lot_group_name': svl.lot_group_id.name if svl.lot_group_id else '',
                    'quantity': svl.quantity,
                    'unit_cost': svl.unit_cost,
                    'value': svl.value,
                    'remaining_qty': svl.remaining_qty,
                    'remaining_value': svl.remaining_value,
                    'account_move_id': svl.account_move_id.id if svl.account_move_id else False,
                    'account_move_name': svl.account_move_id.name if svl.account_move_id else '',
                })
                total_qty += svl.quantity
                total_value += svl.value

            svl_count = len(svl_rows)
            total_pages = max(1, (svl_count + page_size - 1) // page_size)

            # Acumular nos grand totals ANTES de arredondar (evita drift de arredondamento)
            raw_grand_qty += total_qty
            raw_grand_value += total_value

            # Arredondar usando precisão dinâmica de decimal.precision
            # (Product Unit of Measure / Product Price) — elimina resíduos
            # de vírgula flutuante e respeita configuração do utilizador.
            total_qty = float_round(total_qty, precision_digits=qty_precision)
            total_value = float_round(total_value, precision_digits=price_precision)
            # Garantir que -0.0 se torna 0.0
            if float_is_zero(total_qty, precision_digits=qty_precision):
                total_qty = 0.0
            if float_is_zero(total_value, precision_digits=price_precision):
                total_value = 0.0

            # Custo unitário:
            # - Caso normal (qty != 0): média ponderada valor/qty
            # - Produto esgotado (qty = 0 E valor = 0): último SVL cronológico
            #   (mostra o último custo conhecido — informação histórica útil)
            # - Resíduo contabilístico (qty = 0 mas valor != 0): 0
            #   (mostra a "verdade contábil" — o valor residual continua visível
            #    na coluna Valor; custo unit a 0 evita inconsistência aparente)
            if total_qty:
                unit_cost = total_value / total_qty
            elif total_value == 0 and svl_list:
                unit_cost = svl_list[-1].unit_cost
            else:
                unit_cost = 0.0

            groups.append({
                'product_id': pid,
                'product_name': prod.display_name,
                'uom': prod.uom_id.name or '',
                'total_qty': total_qty,
                'total_value': total_value,
                'unit_cost': unit_cost,
                'svls': svl_rows,
                'svl_count': svl_count,
                'total_pages': total_pages,
            })

        groups.sort(key=lambda g: g['product_name'])

        # ── Acrescentar 1º nível: agrupar os produtos por CLASSIFICAÇÃO ──
        # Os dicts de produto (groups) ficam INTACTOS — só são distribuídos
        # por buckets de classificação. O JS de collapse/paginação por produto
        # continua a funcionar tal como está.
        class_sel = dict(self.env['product.template']._fields['product_classification'].selection)
        by_class = defaultdict(list)
        for g in groups:
            prod = self.env['product.product'].browse(g['product_id'])
            cls = prod.product_tmpl_id.product_classification or False
            by_class[cls].append(g)

        classification_groups = []
        for cls in sorted(
            by_class.keys(),
            key=lambda c: class_sel.get(c, 'zzz') if c else 'zzz',
        ):
            prods = by_class[cls]
            cls_qty = float_round(sum(g['total_qty'] for g in prods), precision_digits=qty_precision)
            cls_value = float_round(sum(g['total_value'] for g in prods), precision_digits=price_precision)
            if float_is_zero(cls_qty, precision_digits=qty_precision):
                cls_qty = 0.0
            if float_is_zero(cls_value, precision_digits=price_precision):
                cls_value = 0.0
            classification_groups.append({
                'classification': cls,
                'classification_label': class_sel.get(cls, 'Sem Classificação') if cls else 'Sem Classificação',
                'products': prods,
                'n_products': len(prods),
                'total_qty': cls_qty,
                'total_value': cls_value,
            })

        grand_total_qty = float_round(raw_grand_qty, precision_digits=qty_precision)
        grand_total_value = float_round(raw_grand_value, precision_digits=price_precision)
        if grand_total_qty == 0.0:
            grand_total_qty = 0.0
        if grand_total_value == 0.0:
            grand_total_value = 0.0
        total_svls = sum(g['svl_count'] for g in groups)

        return {
            'is_html_type': report_type == 'html',
            'date': date,
            'product': product,
            'classification': classification,
            'classification_label': classification_label,
            'accounting_filter': accounting_filter,
            'accounting_filter_label': accounting_filter_label,
            'groups': groups,
            'classification_groups': classification_groups,
            'grand_total_qty': grand_total_qty,
            'grand_total_value': grand_total_value,
            'total_svls': total_svls,
            'page_size': page_size,
            'qty_precision': qty_precision,
            'price_precision': price_precision,
            'currency': company.currency_id,
            'company': company,
            'report_date': fields.Datetime.now(),
            'title': 'Valorização de Inventário',
            'docs': [company],
        }
