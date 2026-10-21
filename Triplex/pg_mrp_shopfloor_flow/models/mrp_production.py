# -*- coding: utf-8 -*-
"""Como as operações desta ordem de fabrico se relacionam e quando a produção pode fechar.

Ver o __manifest__.py para o contexto de negócio. Dois assuntos, ambos sobre o fluxo das
operações:
- impedir a cadeia sequencial que o standard cria entre operações (T2);
- dizer ao Chão de Fábrica se a produção já pode ser fechada (T6).
"""
from odoo import Command, api, fields, models

# Estados que contam como operação encerrada.
ESTADOS_ENCERRADOS = ("done", "cancel")


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    pg_pending_workorders = fields.Char(
        string="Operações a concluir",
        compute="_compute_pg_close_state",
        help="Nomes das operações que ainda não estão concluídas. Vazio quando todas estão.",
    )

    pg_can_close = fields.Boolean(
        string="Pode fechar a produção",
        compute="_compute_pg_close_state",
        help="Falso enquanto existirem operações não concluídas nesta ordem de fabrico. O "
             "Chão de Fábrica usa-o para manter o botão de fechar visível mas inactivo.",
    )

    def _link_workorders_and_moves(self):
        # O standard, em `_link_workorders_and_moves`, tem dois ramos: se a BoM declarar
        # dependências (`allow_workorder_dependencies`), respeita-as; senão, atribui a cada
        # ordem `blocked_by_workorder_ids = [ordem anterior]`, formando uma cadeia linear.
        # Desfazemos apenas o segundo caso, para que uma BoM que venha a declarar
        # dependências reais continue a ser respeitada.
        res = super()._link_workorders_and_moves()
        if self.workorder_ids and not self.allow_workorder_dependencies:
            chained = self.workorder_ids.filtered("blocked_by_workorder_ids")
            if chained:
                chained.blocked_by_workorder_ids = [Command.clear()]
        return res

    @api.depends("workorder_ids.state", "workorder_ids.name")
    def _compute_pg_close_state(self):
        for production in self:
            pendentes = production.workorder_ids.filtered(
                lambda w: w.state not in ESTADOS_ENCERRADOS
            )
            production.pg_pending_workorders = ", ".join(pendentes.mapped("name"))
            # Ordens sem operações nenhumas não são bloqueadas. Não é um detalhe: nesta base
            # há centenas de ordens de fabrico sem operações (a produção com operações é a
            # da oficina), e bloqueá-las tornava-as impossíveis de fechar.
            production.pg_can_close = not pendentes
