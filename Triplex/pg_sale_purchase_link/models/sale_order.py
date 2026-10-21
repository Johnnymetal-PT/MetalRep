# -*- coding: utf-8 -*-
"""Liga as compras à encomenda de venda pelo "Documento de Origem" (`origin`).

Duas metades que só funcionam juntas (ver o __manifest__.py para o objetivo de negócio):
1. `action_view_purchase_orders` passa o nome da encomenda como valor por omissão do
   `origin`, para que uma compra criada no "Novo" dessa listagem nasça já com a origem;
2. `_get_purchase_orders` passa a reconhecer o `origin`, para que essa compra volte a
   aparecer na listagem e a contar no smart button.
"""
from odoo import _, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_view_purchase_orders(self):
        """Abre sempre a listagem, mesmo com uma única compra.

        O standard tem dois comportamentos: com várias compras abre a listagem, com uma só
        abre diretamente o formulário dessa compra
        (`sale_purchase/models/sale_order.py:41-51`).

        Esse atalho impede o que este módulo existe para permitir: sem listagem não há botão
        "Novo", logo não há como criar aqui uma compra ligada à encomenda. E é justamente na
        encomenda que já tem uma compra que se vai querer acrescentar a segunda.

        O custo é um toque a mais para quem só quer consultar a única compra existente. Vale
        a troca: uma listagem com uma linha lê-se de imediato, e a alternativa era o botão
        "Novo" nunca aparecer nesse caso.
        """
        action = super().action_view_purchase_orders()
        compras = self._get_purchase_orders()
        action.update({
            "name": _("Purchase Order generated from %s", self.name),
            "view_mode": "tree,form",
            "domain": [("id", "in", compras.ids)],
            "context": {"default_origin": self.name},
        })
        # O standard preenche `res_id` no caso de uma só compra; deixá-lo faria o Odoo abrir
        # o formulário desse registo apesar do `view_mode`.
        action.pop("res_id", None)
        return action

    def _get_purchase_orders(self):
        return super()._get_purchase_orders() | self._pg_purchase_orders_by_origin()

    def _pg_purchase_orders_by_origin(self):
        """Compras cujo `origin` refere o nome de uma destas encomendas.

        Complementa os dois caminhos do standard — `purchase.order.line.sale_line_id`
        (`sale_purchase`) e a cadeia de procurement (`sale_purchase_stock`) — que nenhuma
        compra criada à mão consegue satisfazer.
        """
        Purchase = self.env["purchase.order"]
        names = [name for name in self.mapped("name") if name]
        if not names:
            return Purchase

        # O `origin` do standard pode conter várias origens separadas por ", " (ver
        # purchase_stock/models/stock_rule.py, que junta as origens do procurement na
        # mesma compra). Daí as duas fases: o `ilike` reduz candidatos na base de dados
        # e a comparação decisiva é por token exato — senão `S02530` apanhava também
        # `S025301`.
        domain = expression.OR([[("origin", "ilike", name)] for name in names])
        wanted = set(names)
        return Purchase.search(domain).filtered(
            lambda po: wanted & {part.strip() for part in (po.origin or "").split(",")}
        )
