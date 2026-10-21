# -*- coding: utf-8 -*-
"""Torna as operações iniciáveis sem esperar pela reserva de material.

Ver o __manifest__.py para o contexto de negócio.
"""
import logging

from odoo import Command, models

_logger = logging.getLogger(__name__)

# Tamanho do lote na normalização: escrever nas dependências recalcula o `state` de cada
# ordem, por isso divide-se para não fazer tudo numa só transação de recompute.
LOTE = 200


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def _compute_state(self):
        # O standard distingue dois motivos de espera (ver as etiquetas do campo `state`
        # em `mrp/models/mrp_workorder.py:59-67`):
        #   `pending` — "Waiting for another WO", há uma dependência não concluída;
        #   `waiting` — "Waiting for components", falta material reservado.
        # O Chão de Fábrica esconde do cartão ambos os estados, e é por isso que as
        # operações "desaparecem". Aqui promovemos apenas o segundo caso: sem material a
        # operação continua a ser iniciável, que é o pedido da Triplex (a falta de material
        # é informação a mostrar, não motivo para esconder a operação).
        #
        # O `pending` fica intocado de propósito: se algum dia uma lista de materiais
        # declarar dependências a sério, essa ordem deve continuar a ser respeitada.
        super()._compute_state()
        for workorder in self:
            if workorder.state == "waiting":
                workorder.state = "ready"

    def pg_normalise_shopfloor_states(self):
        """Aplica as duas regras do módulo aos registos que já existiam.

        Método público de propósito: além de correr na instalação, pode ser invocado
        depois de importações de dados ou de qualquer operação que crie ordens de trabalho
        por caminhos que não passem pelo `_link_workorders_and_moves`.

        Idempotente. Só toca em ordens de fabrico que não estejam concluídas ou canceladas.
        """
        Workorder = self.env["mrp.workorder"]
        base = [("production_id.state", "not in", ("done", "cancel"))]

        # 1) Desfazer as cadeias sequenciais inventadas por omissão. Uma lista de materiais
        #    que declare dependências a sério continua a ser respeitada.
        acorrentadas = Workorder.search(base + [("blocked_by_workorder_ids", "!=", False)])
        alvo = acorrentadas.filtered(
            lambda w: not w.production_id.allow_workorder_dependencies
        )
        for inicio in range(0, len(alvo), LOTE):
            alvo[inicio:inicio + LOTE].blocked_by_workorder_ids = [Command.clear()]

        # 2) Promover as que ficaram em `waiting`. Este passo é indispensável e foi o que
        #    faltou na primeira versão: `state` é um campo ARMAZENADO, logo o
        #    `_compute_state` acima só corre quando algo nas suas dependências muda. As
        #    ordens que já estavam em `waiting` sem cadeia nenhuma nunca eram recalculadas
        #    e continuavam escondidas no cartão.
        em_espera = Workorder.search(base + [("state", "=", "waiting")])
        if em_espera:
            self.env.add_to_compute(Workorder._fields["state"], em_espera)
            em_espera.flush_recordset(["state"])

        _logger.info(
            "pg_mrp_shopfloor_flow: %s cadeias desfeitas, %s ordens promovidas de waiting",
            len(alvo), len(em_espera),
        )
        return {"cadeias_desfeitas": len(alvo), "promovidas": len(em_espera)}
