# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Copia list_price → manual_list_price para grupos com use_base_pricing=False.

    O novo campo manual_list_price serve de fonte estável (plain stored) para o
    list_price quando use_base_pricing=False, evitando ciclos de recompute entre
    list_price e margin.
    """
    if not version:
        return

    cr.execute("""
        UPDATE lot_price_group
        SET manual_list_price = list_price
        WHERE use_base_pricing = FALSE
          AND (manual_list_price IS NULL OR manual_list_price = 0)
          AND list_price IS NOT NULL
          AND list_price > 0
    """)
    _logger.info(
        "lot.price.group: migrated %d records list_price → manual_list_price",
        cr.rowcount,
    )
