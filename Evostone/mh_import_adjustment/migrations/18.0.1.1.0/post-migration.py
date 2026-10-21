# -*- coding: utf-8 -*-
"""Migration: popular adjusted_unit_cost em stock.moves OUT afectados por
ADJs já aplicados (state='applied').

Sem isto, ADJs históricos não terão o campo populado → devoluções dos OUTs
abrangidos continuariam a entrar ao unit_cost histórico (sem o ajuste do LC).
"""
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    ADJ = env['import.document.adjustment']
    SVL = env['stock.valuation.layer']
    has_lot_group = 'lot_group_id' in SVL._fields

    adjs = ADJ.search([('state', '=', 'applied'), ('landed_cost_id', '!=', False)])
    _logger.info("Migration adjusted_unit_cost: %d ADJs applied a processar", len(adjs))

    updated_moves = 0
    for adj in adjs:
        imp_done = adj.import_id.reception_date or adj.import_id.date
        if not imp_done:
            continue

        # Timestamp em que o ADJ foi efectivamente aplicado.
        # Só OUTs CRIADOS ANTES disso devem ser tocados pela migration;
        # OUTs posteriores já saíram ao PCMP pós-ADJ (custo correcto).
        adj_apply_dt = (
            adj.cmv_adjustment_move_id.create_date
            or (adj.landed_cost_id and adj.landed_cost_id.create_date)
            or adj.write_date
        )

        # Agregar valuation_adjustment_lines por (product, lot_group)
        per_pg = {}
        for vl in adj.landed_cost_id.valuation_adjustment_lines:
            product = vl.product_id
            qty = vl.quantity
            if not qty:
                continue
            lg_id = False
            if has_lot_group:
                in_svl = vl.move_id.stock_valuation_layer_ids.filtered(lambda l: l.quantity > 0)[:1]
                lg_id = in_svl.lot_group_id.id if in_svl and in_svl.lot_group_id else False
            key = (product.id, lg_id)
            entry = per_pg.setdefault(key, {'product': product, 'lot_group_id': lg_id, 'total_qty': 0.0, 'total_lc': 0.0})
            entry['total_qty'] += qty
            entry['total_lc'] += vl.additional_landed_cost

        for entry in per_pg.values():
            product = entry['product']
            lg_id = entry['lot_group_id']
            total_qty = entry['total_qty']
            total_lc = entry['total_lc']
            if not total_qty or not total_lc:
                continue
            unit_cost_added = total_lc / total_qty

            # SVLs OUT desde imp_done E antes do ADJ ser aplicado
            domain = [
                ('product_id', '=', product.id),
                ('quantity', '<', 0),
                ('create_date', '>=', imp_done),
                ('create_date', '<', adj_apply_dt),
            ]
            if has_lot_group and lg_id:
                domain.append(('lot_group_id', '=', lg_id))
            else:
                lot_ids = adj.import_id.picking_ids.move_ids.move_line_ids.filtered(
                    lambda ml: ml.product_id == product
                ).mapped('lot_id').ids
                if lot_ids:
                    domain.append(('lot_id', 'in', lot_ids))

            out_svls = SVL.search(domain)
            for svl in out_svls:
                out_move = svl.stock_move_id
                if not out_move:
                    continue
                if out_move.adjusted_unit_cost:
                    out_move.adjusted_unit_cost += unit_cost_added
                else:
                    original_uc = abs(svl.unit_cost) or (
                        abs(svl.value) / abs(svl.quantity) if svl.quantity else 0.0
                    )
                    out_move.adjusted_unit_cost = original_uc + unit_cost_added
                updated_moves += 1

    _logger.info("Migration adjusted_unit_cost: actualizados %d stock.moves", updated_moves)
