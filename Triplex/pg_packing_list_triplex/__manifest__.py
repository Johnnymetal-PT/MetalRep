{
    'name': 'Packing List Personalizado',
    'version': '1.0',
    'category': 'Inventory/Inventory',
    'summary': 'Packing list Triplex: volumes, dimensões (até 6), cubicagem e peso por produto, venda e entrega',
    'description': """
Packing List Personalizado (Triplex)
====================================

Objetivo de negócio
-------------------
Gerir a informação de embalagem da Triplex de ponta a ponta: definir no PRODUTO os volumes,
dimensões e peso; e propagar/totalizar esses valores na VENDA e na ENTREGA, com um
assistente de cubicagem para acertos pontuais.

Pré-requisitos
--------------
- Módulos: `base`, `product`, `stock`, `sale`.
- Campos Studio `x_studio_*` no `product.template` e no `stock.move`: volumes, peso, dimensões
  até 6 volumes (comprimento_N/altura_N/largura_N) — criados via Studio.
- Permissões definidas em `security/ir.model.access.csv` para o modelo `cubicagem.wizard`.
- Coerência de unidades nas dimensões (recomendado metros, para obter cubicagem em m³).

Como funciona
-------------
- `product.template`: campos de packing por produto — `packing_volumes`, `packing_weight`,
  dimensões de até 6 volumes (comprimento/altura/largura) e `packing_cubicagem` calculada
  (soma de C x A x L dos primeiros N volumes, N = min(6, nº de volumes)). Validações
  impedem valores negativos. A maioria dos campos é "related" a campos Studio `x_studio_*`.
- `stock.move`: valores de packing por linha de movimento = valor do produto x quantidade.
- `sale.order` / `sale.order.line`: totais na venda e por linha; ao alterar a linha,
  sincroniza os valores para os `stock.move` ligados (via `sale_line_id`).
- `cubicagem.wizard` (assistente): introduz dimensões dos volumes, calcula a cubicagem e
  estima o peso (cubicagem x 80) — ou aceita peso manual — e escreve o resultado de volta
  no movimento e/ou na linha de venda e respetivos movimentos.

Passo a passo de utilização
---------------------------
1. Em cada produto, preencher `packing_volumes` e as dimensões dos volumes (1 a 6).
2. Confirmar uma encomenda — a venda e o picking herdam os valores (totais e por linha).
3. Em qualquer linha de picking, sale.order.line ou no próprio picking, abrir o "Cálculo de
   Cubicagem" para ajustar dimensões/peso pontualmente.
4. Imprimir o packing list / consultar os totais na venda e na entrega.

Exemplo prático
---------------
Sofá com 2 volumes (1.2×0.6×0.8 m e 0.6×0.6×0.4 m) -> cubicagem 0.576 + 0.144 = 0.72 m³.
Numa venda de 3 unidades, o total na encomenda fica 2.16 m³ e o peso estimado (no wizard)
seria 2.16 × 80 ≈ 172,8 kg.

FAQ / Resolução de problemas
----------------------------
- P: O total de cubicagem está a 0.
  R: O produto não tem `packing_volumes` ou as dimensões dos volumes preenchidas.
- P: O wizard não escreve no picking.
  R: Confirmar que abriu o wizard a partir do contexto certo (a partir do picking, de uma
     linha de movimento ou de uma linha de venda — o `default_*` é diferente em cada caso).
- P: Estimativa de peso muito alta/baixa.
  R: O fator 80 (kg / m³) está fixo no wizard; ajustar no código se o seu material tiver
     densidade diferente, ou usar a opção "Peso Manual".
- P: Vejo dois módulos de packing — qual é o "oficial"?
  R: Este (`pg_packing_list_triplex`) é a versão Triplex completa; o `pg_packing_list` é a
     versão mais simples.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Depende de muitos campos Studio `x_studio_*` no produto/movimento.
- O fator de estimativa de peso (cubicagem × 80) está fixo no código do wizard.
- A view `views/sale_order_views.xml` está comentada no manifesto.
- Sobrepõe-se a `pg_packing_list` (validar qual está em uso).
""",
    'author': 'Parâmetro Global',
    'website': 'https://parametro.global',
    'depends': ['base', 'product', 'stock', 'sale'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        #'views/sale_order_views.xml',
        'wizard/cubicagem_wizard_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}

