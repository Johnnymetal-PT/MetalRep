# -*- coding: utf-8 -*-
"""Scanner de duplicados em product.template.

Pertence ao modulo `pg_product_duplicate_scanner`. Adiciona um metodo manual
que percorre todos os product.template e regista no log do servidor os grupos
com `barcode` ou `default_code` duplicados, devolvendo uma notificacao Odoo
com o resumo. So leitura: nao altera registos.
"""
import logging
from collections import defaultdict
from odoo import models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Extensao de `product.template` para o scanner de duplicados."""

    _inherit = "product.template"

    def action_log_duplicate_barcodes_and_codes(self):
        """Escreve no log os duplicados de `barcode` e `default_code`.

        Pensado para correr a partir do botao type="object" e tambem da
        `ir.actions.server` registada em `data/server_action_duplicate_scan.xml`.

        Devolve um `ir.actions.client display_notification` com a contagem dos
        grupos duplicados; o detalhe e sempre enviado para o log do servidor
        (nivel warning) para evitar criar registos auxiliares na BD.
        """
        _logger.info("=== DUPLICATE SCAN START (product.template) ===")

        # ---------------------------
        # Duplicate BARCODE scan
        # ---------------------------
        templates_with_barcode = self.env["product.template"].sudo().search([("barcode", "!=", False)])
        barcode_map = defaultdict(list)
        for tmpl in templates_with_barcode:
            barcode_map[tmpl.barcode].append(tmpl)

        dup_barcodes = {b: tlist for b, tlist in barcode_map.items() if len(tlist) > 1}

        if not dup_barcodes:
            _logger.info("No duplicate barcodes found.")
        else:
            _logger.warning("Duplicate barcodes found: %s groups", len(dup_barcodes))
            for barcode, tlist in dup_barcodes.items():
                _logger.warning(
                    "BARCODE DUPLICATE | barcode=%s | count=%s | templates=%s",
                    barcode,
                    len(tlist),
                    [(t.id, t.display_name, t.default_code) for t in tlist],
                )

        # ---------------------------
        # Duplicate DEFAULT_CODE scan
        # ---------------------------
        templates_with_code = self.env["product.template"].sudo().search([("default_code", "!=", False)])
        code_map = defaultdict(list)
        for tmpl in templates_with_code:
            code_map[tmpl.default_code].append(tmpl)

        dup_codes = {c: tlist for c, tlist in code_map.items() if len(tlist) > 1}

        if not dup_codes:
            _logger.info("No duplicate default_codes found.")
        else:
            _logger.warning("Duplicate default_codes found: %s groups", len(dup_codes))
            for code, tlist in dup_codes.items():
                _logger.warning(
                    "DEFAULT_CODE DUPLICATE | default_code=%s | count=%s | templates=%s",
                    code,
                    len(tlist),
                    [(t.id, t.display_name, t.barcode) for t in tlist],
                )

        _logger.info("=== DUPLICATE SCAN END ===")

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Duplicate scan finished",
                "message": (
                    f"Duplicate barcodes: {len(dup_barcodes)} groups | "
                    f"Duplicate default codes: {len(dup_codes)} groups. "
                    "Check server logs for details."
                ),
                "sticky": False,
                "type": "success" if not dup_barcodes and not dup_codes else "warning",
            },
        }

