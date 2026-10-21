{
    "name": "PG Pricelist - Atributos sem acréscimo",
    "version": "1.0",
    "category": "Sales",
    "summary": "Permite que uma lista de preços não aplique a sua regra aos suplementos de certos atributos (ex.: tecido)",
    "description": """
PG Pricelist - Atributos sem acréscimo
======================================

Objetivo de negócio
-------------------
Na Triplex, a lista "NET 2026" parte do preço da tabela "NET DISPLAY" e soma um acréscimo
(x 1,2368). Esse acréscimo deve incidir sobre o preço base e sobre os suplementos de madeira,
mas NÃO sobre os suplementos de tecido, que ficam iguais aos da tabela NET DISPLAY.
Uma lista de preços standard aplica a regra ao preço total da variante (preço base + todos
os suplementos de atributo) e não distingue atributos. Este módulo acrescenta essa distinção.

Pré-requisitos
--------------
- Módulos: `product`.
- Os suplementos de atributo (`price_extra`) têm de estar calculados nos valores de atributo
  do produto (ex.: módulo `pg_variant_calculation`).

Como funciona
-------------
- `product.pricelist` ganha o campo `pg_exempt_attribute_ids` ("Atributos sem acréscimo da
  lista"), visível no formulário da lista de preços.
- Para uma lista com atributos isentos, as regras de percentagem/fórmula com base no Preço de
  Venda passam a calcular:
      preço = regra(preço da variante - suplementos isentos) + suplementos isentos
  Todos os pontos que usam a lista (cotações, linhas de venda, website, listas de preços)
  passam por `product.pricelist.item._compute_price`, onde a lógica está.
- Listas sem atributos isentos mantêm o cálculo standard.

Passo a passo de utilização
---------------------------
1. Em Vendas > Configuração > Listas de Preços, abrir a lista (ex.: "NET 2026").
2. No campo "Atributos sem acréscimo da lista", escolher os atributos (ex.: "CAT TECIDO").
3. Criar uma cotação com essa lista e um artigo com acabamento de madeira e de tecido:
   o suplemento de tecido não leva o acréscimo da lista.

Exemplo prático
---------------
Preço base 1 000 EUR, madeira +200, tecido +100, regra "preço x 1,25":
- Sem isenção:            (1 000 + 200 + 100) x 1,25 = 1 625
- Tecido isento:          (1 000 + 200) x 1,25 + 100 = 1 600

FAQ / Resolução de problemas
----------------------------
- P: A lista continua a multiplicar o tecido.
  R: Confirmar que o atributo escolhido é exatamente o da variante (ex.: "CAT TECIDO" e não
     "CAT TECIDO EXT"), e que a regra tem base "Preço de Venda" e tipo percentagem/fórmula.
- P: Regras com base noutra lista de preços ou no custo.
  R: Não são tratadas; calculam-se como no standard.

Pontos de atenção
-----------------
- Só trata variantes (product.product) e atributos que criam variante. Atributos "sem variante"
  (no_variant) escolhidos no configurador não são separados.
- Os suplementos isentos são convertidos para a UoM e a moeda do cálculo, tal como o preço base.
""",
    "author": "Parâmetro Global",
    "license": "LGPL-3",
    "depends": ["product"],
    "data": [
        "views/product_pricelist_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
