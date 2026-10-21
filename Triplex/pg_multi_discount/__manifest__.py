# -*- coding: UTF-8 -*-
# Part of Softhealer Technologies.
{
    "name": "All in One Multi Discount",
    "author": "Parametro Global",
    "version": "0.0.4",
    "license": "OPL-1",
    "category": "Extra Tools",
    "summary": "Descontos múltiplos em cascata (ex.: 10+5+3) em vendas, compras e faturas",
    "description": """
All in One Multi Discount
=========================

Origem
------
Módulo de terceiros (Softhealer Technologies, "All in One Multi Discount"), adaptado para
a Triplex. Mantém o prefixo `sh_` nos campos.

Objetivo de negócio
-------------------
O standard do Odoo só permite um desconto por linha. Este módulo permite descontos
sucessivos/em cascata (ex.: desconto de esquema + financeiro + especial), introduzidos num
único campo de texto como "10+5+3".

Pré-requisitos
--------------
- Módulos: `sale`, `sale_management`, `purchase`, `account`.
- Os campos da cascata são visíveis a todos os utilizadores com acesso ao documento
  (as vistas não usam `groups`; ver Pontos de atenção).

Como funciona
-------------
Acrescenta campos `sh_*` às linhas de venda, compra e fatura
(sale.order.line / purchase.order.line / account.move.line):
- `sh_multi_discount` (texto): a cascata de descontos separados por "+".
- Ao alterar (onchange), divide a string por "+" e aplica cada percentagem sucessivamente
  sobre o preço já descontado, calculando:
    * `sh_discount_price_unit`: preço unitário final após todos os descontos
    * `sh_discount_amount`: desconto total por unidade
    * `sh_discounted_total_amount`: desconto total da linha (x quantidade)
  e converte o resultado para o campo standard `discount` (% equivalente único), mantendo
  compatibilidade com o resto do Odoo.
- O desconto é propagado para a fatura/lançamento contabilístico em
  `_prepare_invoice_line` / `_prepare_account_move_line`.
- Relatórios PDF (report/*.xml) mostram a cascata de descontos.
- `sh_show_multi_disc` (no documento): controla se a cascata aparece no PDF.

Passo a passo de utilização
---------------------------
1. Numa cotação/fatura, abrir uma linha e preencher o campo "Multi Discount" com a cascata
   (ex.: "10+5+3").
2. O sistema recalcula `sh_discount_price_unit`, `sh_discount_amount`,
   `sh_discounted_total_amount` e a percentagem equivalente em `discount`.
3. (Opcional) Ativar/desativar `sh_show_multi_disc` para incluir/ocultar a cascata no PDF.
4. Confirmar/Faturar normalmente — os campos `sh_*` viajam para os documentos seguintes.

Exemplo prático
---------------
Linha com preço unitário 100 € e Multi Discount "10+5+3":
- Passo 1: 100 * (1 - 10%) = 90 €
- Passo 2: 90 * (1 - 5%) = 85,50 €
- Passo 3: 85,50 * (1 - 3%) = 82,93 €
Total: `sh_discount_price_unit` = 82,93 €, `discount` ≈ 17,07 %.

FAQ / Resolução de problemas
----------------------------
- P: Coloquei "10+5+3" e o desconto deu errado.
  R: O cálculo é em cascata (não somado): 10+5+3 ≈ 17,07 %, não 18 %.
- P: O campo Multi Discount não aparece nas linhas de compra/fatura.
  R: É uma coluna opcional da lista de linhas; ativá-la no seletor de colunas.
- P: O PDF não mostra a cascata.
  R: Só o PDF da encomenda de VENDA a mostra. Os relatórios de compra e de fatura do
     módulo estão desativados (ver Pontos de atenção).
- P: Alterei a cascata de uma linha importada/criada por API e o desconto não mudou.
  R: O cálculo é um onchange — só corre no formulário. Por importação/API, enviar também
     o `discount` equivalente.
- P: O controlo por grupo não funciona.
  R: É o problema dos xmlids descrito abaixo nos Pontos de atenção.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Ativo em VENDAS, COMPRAS e FATURAS (cliente e fornecedor) desde a 0.0.4. Até aí as
  compras estavam comentadas no manifesto e a vista da fatura usava
  `groups="sh_multi_discount.group_..."`: como esse xmlid não existe, o Odoo removia os
  campos a todos os utilizadores. A 0.0.4 retira os `groups` das vistas de compra e fatura,
  como já estava feito na de venda.
- Relatórios PDF: só o da venda está ativo. O da fatura foi desativado a 2025-01-27 (ver
  report/account_move_templates.xml); o de compra fica desativado porque os relatórios de
  compra desta base foram refeitos no Studio e os XPaths são posicionais.
- Na vista de compra, o readonly do `discount` mantém a regra standard `qty_invoiced != 0`.
- `_compute_dis_bool` verifica grupos com o prefixo do módulo ORIGINAL
  (`sh_multi_discount.group_...`), mas os grupos são definidos neste módulo como
  `pg_multi_discount.group_...`. A verificação não resolve o xmlid, pelo que `dis_bool`
  fica sempre True (controlo por grupo não está a funcionar).
- Existe um `print()` de depuração em models/sale_order.py (resíduo).
""",
    "depends": [
        'sale',
        'sale_management',
        'purchase',
        'account',
        # Fornece `product_variant_desc`, campo que a personalização Studio do formulário
        # de venda referencia. Sem esta dependência o upgrade carrega este módulo antes
        # dele e a validação da vista combinada de `sale.order` falha.
        'pg_product_variant_description_bytesfuel',
        ],
    "data": [
        'security/sale_order_groups.xml',
        'security/purchase_order_groups.xml',
        'security/account_move_groups.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'report/sale_order_templates.xml',
        # Desativado: os relatórios de compra desta base foram refeitos no Studio
        # (report_editor_customization_full) e os XPaths do ficheiro são posicionais
        # (th[3], td[5]) — mesmo problema que partiu o relatório da fatura.
        #'report/purchase_order_templates.xml',
        'report/account_move_templates.xml',
    ],

    "images": ['static/description/background.png', ],
    "auto_install": False,
    "application": True,
    "installable": True,
    "price": 40,
    "currency": "EUR"
}
