# -*- coding: utf-8 -*-
"""Forçar o diário por defeito das faturas de fornecedor.

Contexto HMD
------------
O diário por defeito de uma fatura de fornecedor estava a resolver para
"Custos com Pessoal" em vez de "Faturas de Fornecedor", e o problema NÃO
vinha da ordenação por `sequence` (que já favorece "Faturas de Fornecedor"):
vinha de um `ir.default` em `account.move.journal_id` que impõe o diário
explicitamente.

Como o diário é imposto, o `_compute_journal_id` standard não o substitui
(só recalcula quando o diário atual é de tipo inválido — ver
`account/models/account_move.py`), pelo que um override apenas de
`_search_default_journal` não chega: esse método nem sequer é chamado.

Estratégia (dois pontos, defensivos)
------------------------------------
1. `default_get` (principal): corre DEPOIS do `ir.default` e antes do
   `create`. Tanto a criação manual ("Novo" com `default_move_type`) como
   o fluxo Pedido de Compra → "Criar Fatura de Fornecedor" (que faz
   `with_context(default_move_type='in_invoice')` e cai em
   `_add_missing_default_values → default_get`) passam por aqui. Ao
   reescrever `journal_id` aqui, ganhamos a qualquer `ir.default`.
2. `_search_default_journal` (secundário): cobre o caminho de default
   "limpo" (sem `ir.default`), por robustez.

Em ambos os casos só se atua sobre documentos de compra
(`in_invoice`/`in_refund`) e só se o utilizador atual conseguir mesmo
aceder ao diário configurado (respeita a whitelist de
`pg_account_journal_access`, evitando reintroduzir AccessError). A escolha
manual posterior do utilizador é sempre respeitada.
"""

from odoo import api, models

_VENDOR_TYPES = ("in_invoice", "in_refund")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _pg_target_purchase_journal(self, company):
        """Diário configurado, se existir, for de compra e o user lhe aceder."""
        target = company.sudo().pg_default_purchase_journal_id
        if not target or target.type != "purchase" or target.company_id != company:
            return self.env["account.journal"]
        # search com as regras do utilizador atual = só devolve se acessível.
        return self.env["account.journal"].search(
            [("id", "=", target.id), ("company_id", "=", company.id)], limit=1
        )

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if "journal_id" not in fields_list:
            return vals
        move_type = self.env.context.get("default_move_type") or vals.get("move_type")
        if move_type not in _VENDOR_TYPES:
            return vals
        company_id = (
            self.env.context.get("default_company_id")
            or vals.get("company_id")
            or self.env.company.id
        )
        company = self.env["res.company"].browse(company_id)
        target = self._pg_target_purchase_journal(company)
        if target:
            vals["journal_id"] = target.id
        return vals

    def _search_default_journal(self):
        journal = super()._search_default_journal()
        if "purchase" not in self._get_valid_journal_types():
            return journal
        company = self.company_id or self.env.company
        target = self._pg_target_purchase_journal(company)
        return target or journal
