# -*- coding: utf-8 -*-
{
    "name": "PG MRP Shop Floor Flow",
    "version": "17.0.1.0.0",
    "summary": "Operações de fabrico independentes e iniciáveis em qualquer ordem, sem esperar por material",
    "description": """
PG MRP Shop Floor Flow
======================

Objetivo de negócio
-------------------
A Triplex não produz de forma linear: a mesma peça pode começar pela espuma, pelo corte ou
pelo corte e costura, e volta várias vezes a secções anteriores. O Chão de Fábrica impunha
uma ordem e escondia operações, o que tornava a app inutilizável para a oficina.

Este módulo faz com que as quatro operações (Corte, Costura, Espuma, Estofo) fiquem
visíveis e iniciáveis em qualquer ordem, independentemente da reserva de material. A
Embalagem mantém-se como fase final (o bloqueio do fecho é tarefa separada).

Tarefa: T2 do documento `docs/PRODUCAO_TAREFAS_2026-07-27.md` (Odoo 6628).

Causa-raiz
----------
O campo `state` da ordem de trabalho distingue dois motivos de espera
(`mrp/models/mrp_workorder.py:59-67`):

- `pending` — "Waiting for another WO": existe uma dependência não concluída;
- `waiting` — "Waiting for components": falta material reservado.

O Chão de Fábrica **esconde do cartão ambos** (getter `workorders` em
`enterprise/mrp_workorder/static/src/mrp_display/mrp_display_record.js:223-229`). E as
dependências não vinham de nenhum módulo `pg_`: o standard, em
`_link_workorders_and_moves` (`mrp/models/mrp_production.py:1479-1484`), acorrenta cada
ordem à anterior sempre que a lista de materiais não declara dependências próprias.

Medido em `triplex_test` a 28/07/2026, antes da correção: 1995 ordens de trabalho em 812
ordens de fabrico abertas — 1240 em `pending`, 585 em `waiting`, 161 em `ready`. Das 1995,
1236 estavam acorrentadas, e nenhuma operação de lista de materiais declarava dependências.

Como funciona
-------------
1. `mrp.production._link_workorders_and_moves`: depois de o standard correr, desfaz a
   cadeia **apenas** quando `allow_workorder_dependencies` é falso, isto é, quando a cadeia
   foi inventada por omissão. Uma lista de materiais que declare dependências reais
   continua a ser respeitada.
2. `mrp.workorder._compute_state`: promove `waiting` a `ready`. Sem material a operação
   passa a ser iniciável. O `pending` fica intocado de propósito.
3. `post_init_hook`: limpa as cadeias já existentes nas ordens de fabrico em curso. Não
   toca em ordens concluídas ou canceladas, e é idempotente.

Nada de JavaScript: com as operações em `ready`, o cartão do Chão de Fábrica mostra-as sem
ser preciso alterar o Enterprise.

Passo a passo de utilização
---------------------------
1. Instalar o módulo. A limpeza das cadeias existentes corre na instalação.
2. Abrir o Chão de Fábrica numa ordem de fabrico sem material reservado.
3. As quatro operações aparecem no cartão e qualquer uma pode ser iniciada primeiro.

Exemplo prático
---------------
Uma cadeira cujo casco ainda não chegou: antes, o cartão aparecia vazio e a secção da
Espuma não tinha como registar trabalho. Depois, as quatro operações estão lá e a Espuma
começa pelo que já pode fazer, sem esperar pelo Corte.

FAQ / Resolução de problemas
----------------------------
- P: Uma operação continua a não aparecer.
  R: Verificar o `state` no back office. Se estiver em `pending`, tem uma dependência real
     em `blocked_by_workorder_ids` — o módulo não a remove de propósito.
- P: Como se sabe que falta material, se a operação já aparece?
  R: Pelo campo `production_availability` da ordem de fabrico. Mostrá-lo no cartão é a
     frente que falta da T2.
- P: Podemos voltar a impor uma ordem entre operações?
  R: Sim: activar as dependências na lista de materiais
     (`allow_operation_dependencies`) e declará-las. O módulo respeita-as.

Fechar produção só com todas as fases concluídas (T6, Odoo 6632)
--------------------------------------------------------------
O botão "Fechar produção" do cartão da ordem de fabrico fica **visível e inactivo** enquanto
existirem operações não concluídas, com a lista do que falta ao lado. O cliente foi explícito
quanto a isto na reunião: visível, não escondido. Esconder deixaria o operador sem saber que
o passo existe; desactivado com a razão à frente ensina o que falta fazer.

Herda-se o template do rodapé da **ordem de fabrico** e não o do cartão inteiro, para não
haver confusão com o botão homónimo do cartão da **operação**, que tem outro handler e outro
propósito.

Duas condições em que não se bloqueia, ambas deliberadas:
- **ordens sem operações nenhumas** — nesta base há centenas (a produção com operações é a da
  oficina), e bloqueá-las tornava-as impossíveis de fechar;
- **estado de validação** — nesse momento o mesmo botão passa a ser "Anular", e bloqueá-lo
  impediria o operador de desfazer.

Pontos de atenção
-----------------
- Promover `waiting` a `ready` significa que se pode registar trabalho numa peça cujo
  material não está reservado. Foi um pedido explícito do cliente na reunião de
  27/07/2026 — a alternativa era continuar sem poder planear.
- O bloqueio do fecho é só no ecrã. Fechar a produção pelo back office ou por API continua a
  ser possível, o que é intencional: o gestor de fabrico tem de poder resolver casos presos.
- O módulo não mexe no indicador de falta de material no cartão, que é a frente que falta
  da T2.
""",
    "category": "Manufacturing",
    "author": "Parametro Global",
    "license": "LGPL-3",
    # `mrp_workorder` é a app Chão de Fábrica, onde vive o botão de fechar a produção.
    "depends": ["mrp", "mrp_workorder"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_flow/static/src/js/mrp_display_close_patch.js",
            "pg_mrp_shopfloor_flow/static/src/xml/mrp_display_record.xml",
            "pg_mrp_shopfloor_flow/static/src/scss/close_blocked.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
