# -*- coding: utf-8 -*-
{
    "name": "PG Sale Purchase Link",
    "version": "17.0.1.0.0",
    "summary": "Associa à encomenda de venda as compras criadas a partir do smart button 'Purchase'",
    "description": """
PG Sale Purchase Link
=====================

Objetivo de negócio
-------------------
Na encomenda de venda existe um smart button ("Purchase") que abre a lista das compras
dessa encomenda — o ecrã com o título "Encomenda gerada a partir de S0xxxx". Nessa lista
há um botão "Novo", e o utilizador espera que a compra criada ali fique associada à
encomenda. No standard não fica: a ação não passa contexto nenhum, pelo que a compra
nasce solta e nunca mais reaparece na lista.

Este módulo fecha esse ciclo ao nível da **encomenda** (não da linha de venda).

Pré-requisitos
--------------
- Módulos: `sale_purchase` (instalado; o `sale_purchase_stock` é compatível e complementar).
- Nada a configurar depois da instalação.

Como funciona
-------------
Duas metades, que só resolvem o problema em conjunto:

1. `action_view_purchase_orders` passa a devolver `context` com `default_origin` igual ao
   nome da encomenda. A compra criada no "Novo" nasce com o "Documento de Origem"
   preenchido.
2. `_get_purchase_orders` passa a incluir as compras cujo `origin` refere o nome da
   encomenda. É esta metade que faz a compra reaparecer na lista e contar no smart button.

A segunda metade é indispensável: no standard, uma compra entra nessa lista por
`purchase.order.line.sale_line_id` (módulo `sale_purchase`) ou pela cadeia de procurement
(`sale_purchase_stock`), e uma compra criada à mão não tem nem uma coisa nem outra. Encher
só o `origin` mostrava o valor na coluna mas não ligava nada.

Passo a passo de utilização
---------------------------
1. Instalar o módulo.
2. Abrir uma encomenda de venda que já tenha compras e clicar no smart button "Purchase".
3. Na lista, clicar em "Novo" e preencher a compra. O "Documento de Origem" já vem com o
   número da encomenda.
4. Gravar e voltar à encomenda.
5. Clicar outra vez no smart button: a compra nova está na lista e o contador subiu.

Exemplo prático
---------------
A encomenda S02530 tem duas compras geradas pelo reabastecimento (P04076 e P04077, ambas
com origem S02530). O comprador precisa de encomendar um acabamento que a rota não gerou:
entra pelo smart button, clica "Novo", cria a P04078 e grava. A P04078 fica com origem
S02530 e passa a aparecer ao lado das outras duas.

FAQ / Resolução de problemas
----------------------------
- P: Criei a compra e ela não apareceu logo na lista onde a criei.
  R: É esperado. O domínio dessa lista é um instantâneo de IDs, calculado quando o smart
     button foi clicado. Voltar à encomenda e clicar outra vez no botão mostra-a.
- P: O contador do smart button não subiu.
  R: Recarregar a encomenda. O contador é um campo calculado não armazenado e acerta na
     leitura seguinte.
- P: Apaguei o "Documento de Origem" da compra.
  R: A ligação desaparece — é o `origin` que a sustenta. Voltar a escrever o número da
     encomenda restabelece-a.
- P: A compra é a um fornecedor do grupo (ex.: Oficinna 22) e apareceu uma venda nova.
  R: Comportamento do `pg_intercompany_po_so_sync`, alheio a este módulo: uma compra
     intercompany gera a venda correspondente na outra empresa.

Pontos de atenção
-----------------
- A ligação é **por encomenda**, via campo de texto `origin`, e não substitui a ligação
  estrutural do standard (`purchase.order.line.sale_line_id`), que aponta para uma **linha**
  de venda. Consequência: estas compras não alimentam o `sale_order_id` armazenado nas
  linhas de compra nem os avisos automáticos de cancelamento do `sale_purchase`. Foi uma
  decisão consciente — para o uso pedido (rastreabilidade e reaparecer na lista) basta.
- O `origin` é editável pelo utilizador e não tem integridade referencial. Escrever lá o
  número de uma encomenda cria a ligação; um número errado cria uma ligação errada.
- A comparação é por token exato (o `origin` do standard pode juntar várias origens
  separadas por ", "), pelo que `S02530` não apanha `S025301`.
- O smart button continua escondido quando a encomenda ainda não tem nenhuma compra
  (`invisible="purchase_order_count == 0"`, vista standard do `sale_purchase`). Criar a
  **primeira** compra a partir da encomenda exige tornar o botão sempre visível — fora do
  âmbito deste módulo.
""",
    "category": "Sales",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "depends": ["sale_purchase"],
    "data": [],
    "installable": True,
    "application": False,
}
