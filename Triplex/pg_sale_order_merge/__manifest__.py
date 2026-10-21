# -*- coding: utf-8 -*-
{
    "name": "PG Sale Order Merge",
    "version": "17.0.1.0.0",
    "author": "Parametro Global",
    "category": "Sales",
    "license": "LGPL-3",
    "summary": "Funde várias encomendas/cotações de venda numa só, com regras de "
    "elegibilidade e salvaguardas",
    "description": """
PG Sale Order Merge
===================

Objetivo de negócio
-------------------
Consolidar várias vendas do mesmo cliente numa única encomenda/cotação, evitando
documentos dispersos (equivalente, do lado das Vendas, à fusão de Compras já
existente na instância). Dá origem a um único registo `sale.order` e, no caso de
vendas confirmadas, religa a logística (entregas, produção e compras) à venda
sobrevivente.

Como funciona
-------------
Adiciona uma ação contextual **"Fundir Vendas (PG)"** no menu de Ações das
Vendas (lista e formulário). Sobre a seleção:

1. Valida a **chave de fusão** — só funde vendas iguais, em simultâneo, em:
   empresa, cliente, endereço de entrega, endereço de faturação, lista de
   preços, moeda, posição fiscal e condições de pagamento.
2. Aplica **salvaguardas** (guards):
   - só estados Cotação / Cotação Enviada / Confirmada;
   - vendas confirmadas só se a logística **ainda não foi executada** (sem
     entregas concluídas, sem ordens de produção em curso/concluídas, sem
     compras rececionadas, sem faturas publicadas);
   - **intercompany desativado por defeito** (cliente = empresa do grupo);
     ativável por contexto `pg_allow_intercompany`;
   - **teto de grupo grande** (> 20 vendas) exige contexto
     `pg_confirm_large_merge`.
3. Executa o padrão **sobrevivente + mover linhas**: escolhe a venda de id mais
   baixo como sobrevivente, move as linhas das restantes para ela (preservando
   as linhas originais e, logo, as ligações `stock.move.sale_line_id`), religa a
   logística das confirmadas ao grupo de procurement da sobrevivente e
   **cancela** as vendas de origem (mantendo o registo/número em "Cancelados"),
   com referência cruzada (`pg_merged_into_id`).

Âmbito e limitações
--------------------
- **Cotações (rascunho)**: totalmente suportado e testado.
- **Vendas confirmadas pré-logística**: suportado; o caminho de religação de
  logística (`_pg_relink_downstream`) deve ser validado com um caso confirmado
  real antes de uso em produção. A consolidação é feita ao nível do grupo de
  procurement; uma **entrega física única** pode ainda exigir Transferências em
  Lote (`stock_picking_batch`).
- **Vendas já produzidas/entregues/faturadas**: fora de âmbito (bloqueado pelos
  guards) — reverter operações reais é desaconselhado.

Pré-requisitos
--------------
- Módulos: `sale_management`, `sale_stock`. Integra com `mrp` e `purchase`
  quando instalados (acesso protegido por verificação de modelo no registo).

Notas
-----
- A regra do sobrevivente (id mais baixo = mais antigo) é determinística e pode
  ser ajustada em `action_pg_merge_orders`.
- Recomenda-se disponibilizar apenas a ação **manual** (sem cron), para que a
  fusão seja sempre uma decisão consciente do utilizador.
""",
    "depends": [
        "sale_management",
        "sale_stock",
        # Fornece `product_variant_desc`, campo que a personalização Studio do formulário
        # de venda referencia. Sem esta dependência o upgrade carrega este módulo antes
        # dele e a validação da vista combinada de `sale.order` falha.
        "pg_product_variant_description_bytesfuel",
    ],
    "data": [
        "data/server_action.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
}
