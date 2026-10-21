# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models
from odoo.tools import float_is_zero, float_round


class StockAtDateReport(models.AbstractModel):
    _name = 'report.mh_stock_at_date.report'
    _description = 'Relatório de Inventário a uma Data'

    @api.model
    def get_locations(self):
        """Devolve localizações internas/transit para o dropdown."""
        locs = self.env['stock.location'].search([
            ('usage', '=', 'internal'),
        ])
        return [{'id': l.id, 'name': l.complete_name} for l in locs]

    @api.model
    def get_products(self):
        """Devolve produtos stockable para autocomplete."""
        prods = self.env['product.product'].search_read(
            [('is_storable', '=', True)],
            ['id', 'display_name'],
        )
        out = [{'id': p['id'], 'name': p['display_name']} for p in prods]
        out.sort(key=lambda p: (p['name'] or '').lower())
        return out

    @api.model
    def get_classifications(self):
        """Devolve selection de product_classification para dropdown."""
        fields_info = self.env['product.template'].fields_get(
            ['product_classification'], attributes=['selection'])
        sel = (fields_info.get('product_classification') or {}).get('selection') or []
        return [{'value': v, 'label': l} for v, l in sel]

    @api.model
    def get_html(self, data):
        """Devolve HTML renderizado com filtros aplicados."""
        render_values = self._get_report_data(data or {})
        html = self.env['ir.qweb']._render(
            'mh_stock_at_date.report_stock_at_date_page',
            render_values,
        )
        return {
            'html': html,
            'total_groups': len(render_values['groups']),
            'total_lines': render_values['grand_lines'],
            'grand_total': render_values['grand_total'],
        }

    def _get_report_data(self, data):
        # Precisão dinâmica — Definições → Técnico → Precisão Decimal
        qty_precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # ── Parse params ──
        date_str = data.get('date')
        if date_str:
            # Date input → fim do dia para mostrar stock após todos movimentos
            target_date = fields.Datetime.to_datetime(date_str).replace(
                hour=23, minute=59, second=59
            )
        else:
            target_date = fields.Datetime.now()

        location_id = data.get('location_id')
        location_id = int(location_id) if location_id else False
        product_id = data.get('product_id')
        product_id = int(product_id) if product_id else False
        lot_id = data.get('lot_id')
        lot_id = int(lot_id) if lot_id else False
        classification = data.get('classification') or False

        Location = self.env['stock.location']
        filter_location = Location.browse(location_id) if location_id else Location
        filter_product = (
            self.env['product.product'].browse(product_id) if product_id else False
        )
        filter_lot = (
            self.env['stock.lot'].browse(lot_id) if lot_id else False
        )
        classification_label = ''
        if classification:
            sel = dict(self.env['product.template']._fields['product_classification'].selection)
            classification_label = sel.get(classification, '')

        # ── Locations a considerar ──
        if filter_location:
            location_ids = Location.search([
                ('id', 'child_of', filter_location.id),
                ('usage', '=', 'internal'),
            ]).ids
        else:
            location_ids = Location.search([
                ('usage', '=', 'internal'),
            ]).ids

        rows = []
        if location_ids:
            rows = self._query_stock(target_date, location_ids, filter_product, filter_lot, classification)

        # ── Pre-fetch para template ──
        Product = self.env['product.product']
        Lot = self.env['stock.lot']
        prod_ids = list({r['product_id'] for r in rows if r['product_id']})
        loc_ids = list({r['location_id'] for r in rows if r['location_id']})
        lot_ids_used = list({r['lot_id'] for r in rows if r['lot_id']})
        products = {p.id: p for p in Product.browse(prod_ids)}
        locations = {l.id: l for l in Location.browse(loc_ids)}
        lots = {l.id: l for l in Lot.browse(lot_ids_used)}

        # ── Agrupar por location → product → lots ──
        by_loc_prod = defaultdict(lambda: defaultdict(list))
        for r in rows:
            by_loc_prod[r['location_id']][r['product_id']].append({
                'lot': lots.get(r['lot_id']) if r['lot_id'] else None,
                'qty': r['qty'],
            })

        form_plural = {
            'block': 'blocos',
            'slab': 'placas',
            'strip': 'bandas',
            'tiles': 'ladrilhos',
            'none': 'unidades',
        }

        groups = []
        raw_grand = 0.0
        for loc_id in sorted(
            by_loc_prod.keys(),
            key=lambda x: locations[x].complete_name if x in locations else ''
        ):
            location = locations.get(loc_id)
            prod_subgroups = []
            raw_loc_total = 0.0
            for prod_id, lot_items in by_loc_prod[loc_id].items():
                product = products.get(prod_id)
                # Arredondar lots para display
                for li in lot_items:
                    li['qty'] = float_round(li['qty'], precision_digits=qty_precision)
                    if float_is_zero(li['qty'], precision_digits=qty_precision):
                        li['qty'] = 0.0
                raw_prod_total = sum(i['qty'] for i in lot_items)
                raw_loc_total += raw_prod_total
                prod_total = float_round(raw_prod_total, precision_digits=qty_precision)
                if float_is_zero(prod_total, precision_digits=qty_precision):
                    prod_total = 0.0
                pf = getattr(product, 'product_form', 'none') if product else 'none'
                prod_subgroups.append({
                    'product': product,
                    'product_id': prod_id,
                    'lots': lot_items,
                    'total_qty': prod_total,
                    'n_lots': len(lot_items),
                    'form_label': form_plural.get(pf, 'unidades'),
                })
            prod_subgroups.sort(key=lambda g: g['product'].display_name if g['product'] else '')
            raw_grand += raw_loc_total
            loc_total = float_round(raw_loc_total, precision_digits=qty_precision)
            if float_is_zero(loc_total, precision_digits=qty_precision):
                loc_total = 0.0
            groups.append({
                'location': location,
                'location_id': loc_id,
                'products': prod_subgroups,
                'total_qty': loc_total,
                'n_products': len(prod_subgroups),
                'n_lots': sum(g['n_lots'] for g in prod_subgroups),
            })

        grand_total = float_round(raw_grand, precision_digits=qty_precision)
        if float_is_zero(grand_total, precision_digits=qty_precision):
            grand_total = 0.0

        return {
            'company': self.env.company,
            'target_date': target_date,
            'filter_location': filter_location,
            'filter_product': filter_product,
            'filter_lot': filter_lot,
            'classification': classification,
            'classification_label': classification_label,
            'groups': groups,
            'grand_total': grand_total,
            'grand_lines': sum(g['n_lots'] for g in groups),
            'qty_precision': qty_precision,
        }

    def _query_stock(self, target_date, location_ids, product, lot, classification=False):
        """Mesmo algoritmo do Odoo nativo: parte do stock.quant ACTUAL e
        reverte moves done com date > target_date (subtrai IN, soma OUT).

        Para target_date >= agora → revert vazio → match exacto com
        stock.quant (= o que o Odoo nativo mostra).
        Para histórico → desfaz movimentos posteriores à data."""
        # Construir filtros opcionais
        prod_clause_q = ''
        prod_clause_sml = ''
        prod_params = []
        if product:
            prod_clause_q += ' AND q.product_id = %s'
            prod_clause_sml += ' AND sml.product_id = %s'
            prod_params.append(product.id)
        if lot:
            prod_clause_q += ' AND q.lot_id = %s'
            prod_clause_sml += ' AND sml.lot_id = %s'
            prod_params.append(lot.id)
        tmpl_filter = ' AND pt.is_storable = TRUE'
        tmpl_params = []
        if classification:
            tmpl_filter += ' AND pt.product_classification = %s'
            tmpl_params.append(classification)

        # Params: 1ª CTE (current_quants), depois 2 SELECTs do revert_moves
        params = [
            tuple(location_ids), *prod_params, *tmpl_params,
            target_date, tuple(location_ids), *prod_params, *tmpl_params,
            target_date, tuple(location_ids), *prod_params, *tmpl_params,
        ]
        query = f"""
            WITH current_quants AS (
                SELECT q.product_id, q.location_id, q.lot_id, SUM(q.quantity) AS qty
                FROM stock_quant q
                JOIN product_product pp ON pp.id = q.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE q.location_id IN %s
                  {prod_clause_q}
                  {tmpl_filter}
                GROUP BY q.product_id, q.location_id, q.lot_id
            ),
            revert_moves AS (
                SELECT product_id, location_id, lot_id, SUM(qty) AS qty FROM (
                    SELECT sml.product_id, sml.location_dest_id AS location_id,
                           sml.lot_id, -sml.quantity AS qty
                    FROM stock_move_line sml
                    JOIN product_product pp ON pp.id = sml.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE sml.state = 'done' AND sml.date > %s
                      AND sml.location_dest_id IN %s
                      {prod_clause_sml}
                      {tmpl_filter}
                    UNION ALL
                    SELECT sml.product_id, sml.location_id, sml.lot_id,
                           sml.quantity AS qty
                    FROM stock_move_line sml
                    JOIN product_product pp ON pp.id = sml.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    WHERE sml.state = 'done' AND sml.date > %s
                      AND sml.location_id IN %s
                      {prod_clause_sml}
                      {tmpl_filter}
                ) t
                GROUP BY product_id, location_id, lot_id
            )
            SELECT
                COALESCE(c.product_id, r.product_id) AS product_id,
                COALESCE(c.location_id, r.location_id) AS location_id,
                COALESCE(c.lot_id, r.lot_id) AS lot_id,
                (COALESCE(c.qty, 0) + COALESCE(r.qty, 0)) AS qty
            FROM current_quants c
            FULL OUTER JOIN revert_moves r
              ON c.product_id = r.product_id
              AND c.location_id = r.location_id
              AND COALESCE(c.lot_id, 0) = COALESCE(r.lot_id, 0)
            WHERE (COALESCE(c.qty, 0) + COALESCE(r.qty, 0)) > 0
            ORDER BY location_id, product_id, lot_id
        """
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
