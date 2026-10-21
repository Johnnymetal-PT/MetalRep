# -*- coding: utf-8 -*-
from . import models


def _post_init_backfill(env):
    """Cria uma pg.planeamento.line para cada sale.order.line existente."""
    SOL = env['sale.order.line']
    PL = env['pg.planeamento.line']
    already_linked = PL.search([]).mapped('sale_line_id').ids
    pending = SOL.search([('id', 'not in', already_linked)])
    if pending:
        PL.create([{'sale_line_id': l.id} for l in pending])
