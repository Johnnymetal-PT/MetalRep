# -*- coding: utf-8 -*-
"""Propaga preço e descontos das linhas de Fatura de Fornecedor para a linha da PO.

Quando a Fatura de Fornecedor é criada a partir de uma Ordem de Compra, cada linha guarda
a ligação à respetiva linha da PO (`purchase_line_id`). Ao editar o preço unitário ou o
desconto na linha da fatura, este módulo escreve esses valores na linha da PO, mantendo a
PO alinhada com o que foi efetivamente faturado. Ver o __manifest__.py.
"""
from odoo import api, models
from odoo.tools import float_compare

# Campos cuja alteração na fatura dispara a propagação para a PO.
PG_TRIGGER_FIELDS = {'price_unit', 'discount', 'sh_multi_discount'}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def _pg_sync_price_to_po(self):
        """Escreve preço e descontos das linhas de fatura de fornecedor na linha da PO."""
        for line in self:
            po_line = line.purchase_line_id
            if not po_line:
                continue
            if line.move_id.move_type not in ('in_invoice', 'in_refund'):
                continue
            vals = {}
            rounding = (line.currency_id or po_line.currency_id).rounding or 0.01
            if float_compare(po_line.price_unit, line.price_unit,
                             precision_rounding=rounding) != 0:
                vals['price_unit'] = line.price_unit
            if float_compare(po_line.discount, line.discount,
                             precision_rounding=0.0001) != 0:
                vals['discount'] = line.discount
            # Cascata de descontos (pg_multi_discount), só se o campo existir em ambos.
            if 'sh_multi_discount' in line._fields and 'sh_multi_discount' in po_line._fields:
                if (po_line.sh_multi_discount or '') != (line.sh_multi_discount or ''):
                    vals['sh_multi_discount'] = line.sh_multi_discount or False
            if vals:
                # Contexto-guarda para evitar reentrância na cadeia de escrita.
                po_line.with_context(pg_skip_po_price_sync=True).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        # No fluxo "Completar Automaticamente", as linhas são CRIADAS (não escritas) já
        # com o preço/desconto eventualmente ajustado, por isso é preciso propagar aqui.
        lines = super().create(vals_list)
        if not self.env.context.get('pg_skip_po_price_sync'):
            lines._pg_sync_price_to_po()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if PG_TRIGGER_FIELDS & set(vals) and not self.env.context.get('pg_skip_po_price_sync'):
            self._pg_sync_price_to_po()
        return res
