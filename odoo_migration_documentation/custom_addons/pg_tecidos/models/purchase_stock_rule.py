# -*- coding: utf-8 -*-
"""Propaga distribuicao analitica da venda/MO para compras geradas pelo MTO.

Resolve lacunas no fluxo standard quando a PO nasce de regras de stock e
precisa herdar a analitica de origem para controlo financeiro.
"""
import logging
import re

from odoo import api, models

_logger = logging.getLogger(__name__)


def _dist_from_analytic_account(account):
    """Convert a single analytic account to a 100% analytic_distribution dict."""
    if not account:
        return {}
    return {str(account.id): 100.0}


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model_create_multi
    def create(self, vals_list):
        # Regra: a PO deve nascer com analitica, mesmo quando criada por
        # automatismos de procurement (sem contexto funcional direto da SO).
        _logger.info("[PO ANALYTIC] purchase.order.create called for %s vals", len(vals_list))
        orders = super().create(vals_list)

        for po in orders:
            if po.analytic_distribution:
                _logger.info("[PO ANALYTIC] PO %s already has analytic_distribution -> skip", po.name)
                continue

            _logger.info(
                "[PO ANALYTIC] Starting analytic_distribution autofill for PO=%s (id=%s) origin=%s fp_origem=%s group_id=%s",
                po.name,
                po.id,
                po.origin,
                getattr(po, "x_studio_fp_origem", None),
                po.group_id.id if po.group_id else None,
            )

            dist = po._pg_get_analytic_distribution_from_sources()

            if dist:
                po.write({"analytic_distribution": dist})
                _logger.info("[PO ANALYTIC] Applied analytic_distribution to PO %s -> %s", po.name, dist)
            else:
                _logger.warning(
                    "[PO ANALYTIC] Could not determine analytic_distribution for PO %s (origin=%s group_id=%s fp_origem=%s)",
                    po.name,
                    po.origin,
                    po.group_id.id if po.group_id else None,
                    getattr(po, "x_studio_fp_origem", None),
                )

        return orders

    def _pg_get_analytic_distribution_from_sources(self):
        """Try: MO by procurement group -> MO by origin -> SO by fp_origem -> SO by origin."""
        self.ensure_one()

        # Ordem de pesquisa e deliberada: primeiro objetos "mais proximos" da
        # origem operacional da PO (MO/group), depois fallback para SO.

        # 1) MO by procurement group
        if self.group_id:
            mo = self.env["mrp.production"].search(
                [("procurement_group_id", "=", self.group_id.id)],
                order="id desc",
                limit=1,
            )
            if mo:
                _logger.info(
                    "[PO ANALYTIC] Found MO by procurement group: MO=%s (id=%s) dist=%s",
                    mo.name, mo.id, mo.analytic_distribution
                )
                if mo.analytic_distribution:
                    return mo.analytic_distribution

        # 2) MO by origin
        mo_name = self._pg_extract_mo_name(self.origin)
        if mo_name:
            mo = self.env["mrp.production"].search([("name", "=", mo_name)], limit=1)
            if mo:
                _logger.info(
                    "[PO ANALYTIC] Found MO by origin: origin=%s MO=%s (id=%s) dist=%s",
                    self.origin, mo.name, mo.id, mo.analytic_distribution
                )
                if mo.analytic_distribution:
                    return mo.analytic_distribution

        # 3) SO by x_studio_fp_origem
        fp = getattr(self, "x_studio_fp_origem", False)
        if fp:
            so = self.env["sale.order"].search([("name", "=", fp)], limit=1)
            if so:
                _logger.info(
                    "[PO ANALYTIC] Found SO by fp_origem: fp=%s SO=%s (id=%s) analytic_account_id=%s",
                    fp, so.name, so.id, so.analytic_account_id.id if so.analytic_account_id else None
                )
                dist = _dist_from_analytic_account(so.analytic_account_id)
                if dist:
                    return dist

        # 4) SO by origin
        if self.origin:
            so = self.env["sale.order"].search([("name", "=", self.origin)], limit=1)
            if so:
                _logger.info(
                    "[PO ANALYTIC] Found SO by origin: origin=%s SO=%s (id=%s) analytic_account_id=%s",
                    self.origin, so.name, so.id, so.analytic_account_id.id if so.analytic_account_id else None
                )
                dist = _dist_from_analytic_account(so.analytic_account_id)
                if dist:
                    return dist

        return {}

    @staticmethod
    def _pg_extract_mo_name(origin):
        # Parse conservador: usamos apenas formato WH/MO/<numero> que existe
        # hoje no projeto para evitar falsos positivos em textos livres.
        if not origin:
            return None
        m = re.search(r"(WH/MO/\d+)", origin)
        return m.group(1) if m else None


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("[PO LINE ANALYTIC] purchase.order.line.create called for %s vals", len(vals_list))
        lines = super().create(vals_list)

        # IMPORTANTE: este override corre num caminho usado por modulos
        # enterprise; devolver recordset e obrigatorio.
        for line in lines:
            if line.analytic_distribution:
                _logger.info("[PO LINE ANALYTIC] POL %s already has analytic_distribution -> skip", line.id)
                continue

            po = line.order_id
            if not po:
                _logger.warning("[PO LINE ANALYTIC] POL %s has no order_id -> skip", line.id)
                continue

            dist = po.analytic_distribution or po._pg_get_analytic_distribution_from_sources()

            _logger.info("[PO LINE ANALYTIC] Autofill POL id=%s PO=%s -> dist=%s", line.id, po.name, dist)

            if dist:
                line.write({"analytic_distribution": dist})
                _logger.info("[PO LINE ANALYTIC] Applied analytic_distribution on POL %s -> %s", line.id, dist)
            else:
                _logger.warning("[PO LINE ANALYTIC] Could not determine analytic_distribution for POL %s (PO=%s)", line.id, po.name)

        return lines
