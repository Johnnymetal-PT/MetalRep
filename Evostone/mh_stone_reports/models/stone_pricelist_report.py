from odoo import api, fields, models


class StonePricelistReport(models.AbstractModel):
    _name = 'report.mh_stone_reports.report_stone_pricelist'
    _description = 'Relatório de Lista de Preços de Pedras'

    def _get_report_values(self, docids, data):
        """Renderização para PDF (via ir.actions.report)."""
        return self._get_report_data(data or {}, 'pdf')

    @api.model
    def get_html(self, data):
        """Renderização para preview HTML no JS."""
        render_values = self._get_report_data(data or {}, 'html')
        return self.env['ir.qweb']._render(
            'mh_stone_reports.report_stone_pricelist_page',
            render_values,
        )

    def _get_report_data(self, data, report_type='html'):
        active_ids = data.get('active_ids') or []
        if active_ids:
            stones = self.env['stone.stock'].browse(active_ids)
        else:
            stones = self.env['stone.stock'].search([])

        # Filtro opcional por artigo (product.product)
        product_id = data.get('product_id')
        product_id = product_id and int(product_id)
        product = self.env['product.product'].browse(product_id).exists() if product_id else False
        if product:
            stones = stones.filtered(lambda s: s.product_id and s.product_id.id == product.id)

        # Pricelist opcional (product.pricelist)
        pricelist_id = data.get('pricelist_id')
        pricelist_id = pricelist_id and int(pricelist_id)
        pricelist = self.env['product.pricelist'].browse(pricelist_id).exists() if pricelist_id else False

        # Agrupar por lot.price.group (pedras com mesmo grupo têm mesma dimensão e preço)
        groups = {}
        for stone in stones:
            pg = stone.price_group_id
            if not pg:
                continue
            if pg.id not in groups:
                groups[pg.id] = {
                    'price_group': pg,
                    'stone_count': 0,
                    'sample_stone': stone,
                }
            groups[pg.id]['stone_count'] += 1

        rows_data = [self._get_group_data(g['price_group'], g['sample_stone'], g['stone_count'], pricelist)
                     for g in groups.values()]
        rows_data.sort(key=lambda r: r['description'])

        company = self.env.company
        grand_total = sum(r['total_price'] for r in rows_data)
        return {
            'is_html_type': report_type == 'html',
            'display_pricelist_title': bool(data.get('display_pricelist_title', False)),
            'product': product,
            'pricelist': pricelist,
            'rows': rows_data,
            'grand_total': grand_total,
            'currency': pricelist.currency_id if pricelist else company.currency_id,
            'company': company,
            'report_date': fields.Datetime.now(),
            'title': 'Lista de Preços',
            'docs': [company],
        }

    def _get_group_data(self, price_group, sample_stone, stone_count, pricelist=False):
        """Uma linha por lot.price.group (todas as pedras do grupo têm mesma dimensão/preço).

        Se pricelist for indicada, usa o preço da pricelist para o produto;
        caso contrário usa o list_price do lot.price.group.
        """
        uom_name = sample_stone.product_id.uom_id.name if sample_stone.product_id and sample_stone.product_id.uom_id else 'm²'
        area = price_group.area or 0.0

        if pricelist and sample_stone.product_id:
            try:
                pl = pricelist
                if sample_stone.lot_id:
                    pl = pricelist.with_context(lot_id=sample_stone.lot_id.id)
                rule_id = pl._get_product_rule(sample_stone.product_id, quantity=1.0)
                if rule_id:
                    unit_price = pl._get_product_price(sample_stone.product_id, 1.0)
                    rule = self.env['product.pricelist.item'].browse(rule_id)
                    # Para regras 'percentage' o Odoo 18 devolve o preço BASE
                    # (o desconto seria aplicado no campo discount da linha de venda).
                    # Para o relatório queremos o preço FINAL, por isso aplicamos manualmente.
                    if rule.compute_price == 'percentage' and rule.percent_price:
                        unit_price = unit_price * (1 - (rule.percent_price / 100.0))
                else:
                    # Pricelist sem regra aplicável → usar preço do lot.price.group
                    unit_price = price_group.list_price or 0.0
            except Exception:
                unit_price = price_group.list_price or 0.0
        else:
            unit_price = price_group.list_price or 0.0

        return {
            'price_group_id': price_group.id,
            'description': price_group.description or sample_stone.description or '',
            'area': area,
            'uom': uom_name,
            'unit_price': unit_price,
            'total_price': unit_price * area,
            'stone_count': stone_count,
        }
