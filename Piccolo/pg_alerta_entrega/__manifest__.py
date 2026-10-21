# -*- coding: utf-8 -*-
{
    "name": "PG Alertas de Entrega (Venda)",
    "version": "17.0.1.0.0",
    "depends": ["sale"],
    "author": "Parametro Global",
    "category": "Sales",
    "summary": "Cria atividades de alerta na Venda a 15, 7 e 1 dia(s) antes da "
               "Data de Entrega (commitment_date), enquanto a venda nao estiver "
               "totalmente faturada, para os utilizadores configurados.",
    "data": [
        "data/pg_alerta_entrega_data.xml",
    ],
    "description": """
PG Alertas de Entrega (Venda)
=============================

a) Objetivo
-----------
O utilizador preenche na Venda a "Data de Entrega" (``commitment_date``).
Enquanto a venda **nao estiver totalmente faturada**
(``invoice_status != 'invoiced'``), o sistema cria atividades de alerta na
propria Venda a **15**, **7** e **1** dia(s) antes dessa data, para os
utilizadores internos configurados (por defeito Carlo e Pedro).

b) Como funciona
----------------
- Acao agendada diaria (``ir.cron``) que chama
  ``sale.order._pg_cron_alertas_entrega()``.
- Para cada venda confirmada com ``commitment_date`` e ainda nao
  totalmente faturada, calcula os dias que faltam ate a data de entrega
  (no fuso do utilizador) e, se forem 15/7/1, agenda uma atividade "To
  Do" por cada utilizador destinatario.
- Destinatarios: parametro do sistema ``pg_alerta_entrega.user_ids``
  (lista de IDs separada por virgulas, por defeito ``6,11``). So sao
  considerados utilizadores internos ativos.
- Anti-duplicados: nao cria a atividade se ja existir uma com o mesmo
  resumo para a mesma venda/utilizador (o resumo inclui os dias).

c) Configuracao
---------------
- Definicoes > Tecnico > Parametros do Sistema:
  ``pg_alerta_entrega.user_ids`` = ``6,11`` (editar para mudar destinatarios).
- Definicoes > Tecnico > Acoes Agendadas: "PG: Alertas de entrega (Venda)".

d) Pontos de atencao
--------------------
- Depende da acao agendada correr diariamente; se o servidor estiver em
  baixo no dia exato de um limiar, esse alerta desse dia nao e criado.
- A comparacao de datas usa o fuso do utilizador da acao agendada.
""",
    "installable": True,
    "application": False,
}
