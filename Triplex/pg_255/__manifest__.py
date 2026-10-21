{
    'name': 'PG 255 Pricelist Formula',
    'version': '1.0',
    'summary': 'Aplica as fórmulas de preço "255" e "Maison Dorée" às listas de preços marcadas (checkbox Studio)',
    'description': """
PG 255 Pricelist Formula
========================

Objetivo de negócio
-------------------
A Triplex tem duas tabelas de preço com fórmulas próprias — "255" e "Maison Dorée". Em vez
de criar regras de pricelist manuais, marca-se a lista de preços com uma das checkboxes
(campos Studio) e o preço é calculado automaticamente a partir do preço base do produto.

Pré-requisitos
--------------
- Módulos: `sale`, `product`.
- Campos Studio na `product.pricelist`: `x_studio_255` (Boolean) e `x_studio_maison_dore`
  (Boolean). Têm de existir criados via Odoo Studio — este módulo não os define.
- Produtos com preço base (`list_price`) coerente — a fórmula assenta nesse valor.

Como funciona
-------------
Estende dois modelos:
- `product.pricelist._compute_price_rule()`: após obter o preço base do Odoo, se a lista
  tiver `x_studio_255` ou `x_studio_maison_dore` ativo, recalcula:
    * 255:           preço = (base / 2) * 2.55
    * Maison Dorée:  preço = (((preço_255 * 0.5) * 0.7) * 11)
  Inclui salvaguardas para chamadas sem lista de preços válida (ex.: snippets do website).
- `sale.order.line._compute_price_unit()`: reaplica a mesma fórmula ao `price_unit` das
  linhas de venda, para garantir coerência com o cálculo da pricelist.

Passo a passo de utilização
---------------------------
1. Em Vendas > Configuração > Listas de Preços, abrir a lista pretendida.
2. Marcar `x_studio_255` OU `x_studio_maison_dore` (NUNCA os dois ao mesmo tempo).
3. Em qualquer ecrã que use a lista (cotação, website, configurador), o preço passa a ser
   o resultado da fórmula.
4. Para confirmar, criar uma cotação com essa lista — verificar o `price_unit` calculado.

Exemplo prático
---------------
Produto com `list_price` = 100 €.
- Lista marcada com `x_studio_255` -> preço = (100 / 2) * 2.55 = 127,50 €.
- Lista marcada com `x_studio_maison_dore` -> preço = (((127,50 * 0.5) * 0.7) * 11) ≈ 490,88 €.

FAQ / Resolução de problemas
----------------------------
- P: A lista está marcada mas o preço não muda.
  R: Os campos Studio podem não existir ainda nesta BD. Confirmar em Studio > res.partner ?
     NÃO — confirmar em Studio sobre `product.pricelist` (x_studio_255, x_studio_maison_dore).
- P: Marquei as duas checkboxes ao mesmo tempo, o que acontece?
  R: A 255 ganha (testada primeiro no código). Convém escolher só uma.
- P: O preço na linha de venda não bate com o da pricelist.
  R: O `_compute_price_unit` foi feito precisamente para o evitar; confirmar que o módulo
     está instalado e a venda foi recalculada (alterar quantidade força recálculo).

Pontos de atenção
-----------------
- A view `views/pricelist_views.xml` está comentada no manifesto (não é carregada).
- Os multiplicadores das fórmulas estão fixos no código; alterações de negócio exigem mudar o módulo.
- O log do servidor recebe um INFO por linha quando a fórmula dispara — útil para auditoria.
""",
    'author': 'Your Name',
    'category': 'Sales',
    'depends': ['sale', 'product'],
    'data': [
        #'views/pricelist_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

