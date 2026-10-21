# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Copia list_price → manual_list_price para product.template com
    product_form='none' (produtos que não usam base.lot.group).

    O novo campo manual_list_price serve de fonte estável (plain stored) para o
    list_price, evitando ciclos de recompute entre list_price e margin.
    """
    if not version:
        return

    cr.execute("""
        UPDATE product_template
        SET manual_list_price = list_price
        WHERE product_form = 'none'
          AND (manual_list_price IS NULL OR manual_list_price = 0)
          AND list_price IS NOT NULL
          AND list_price > 0
    """)
    _logger.info(
        "product.template: migrated %d records list_price → manual_list_price",
        cr.rowcount,
    )
