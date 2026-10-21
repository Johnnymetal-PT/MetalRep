{
    "name": "PG Product Attribute Price Extra Calculation",
    "version": "1.0",
    "depends": ["product"],
    "author": "Your Name",
    "category": "Product",
    "summary": "Calcula automaticamente o price_extra dos atributos e o preço de venda do produto a partir de m², margens e preços de fornecedor",
    "license": "AGPL-3",
    "description": """
PG Product Attribute Price Extra Calculation
============================================

Objetivo de negócio
-------------------
Automatizar o cálculo de preços para evitar erros e contas manuais:
1) o suplemento de preço por valor de atributo (price_extra) a partir de m², corte e margens;
2) o preço de venda do produto (list_price) a partir do custo de fornecedor e margens.

Pré-requisitos
--------------
- Módulos: `product`.
- Nos VALORES DE ATRIBUTO (product.template.attribute.value), preencher: preço por m²,
  m² da peça, valor do corte, margem e margem geral.
- Nos PRODUTOS, preencher os campos Studio de margem (x_studio_margem, x_studio_margem_2_2)
  e ter fornecedores (seller_ids) com preço.

Como funciona
-------------
- `product.template.attribute.value`:
    * Campos de entrada: preco_por_m2, m2_da_peca, valor_do_corte, margem, margem_geral.
    * `price_extra` (calculado): se TODOS os fatores forem 0 -> 0; caso contrário
      price_extra = preco_por_m2 * m2_da_peca * margem * margem_geral + valor_do_corte
      (valores 0 nos multiplicadores são tratados como 1, exceto o corte que é somado).
- `product.template`:
    * `x_studio_valor_interno` (calculado) = soma(preços fornecedor) * margem, arredondado p/ cima.
    * `list_price` (PREÇO DE VENDA, calculado e armazenado) = soma(preços fornecedor) *
      margem * margem extra, arredondado para cima.

Passo a passo de utilização
---------------------------
1. Definir as margens e os preços de fornecedor do produto.
2. Preencher, em cada valor de atributo, o m², corte e margens.
3. Os preços (price_extra, valor interno, preço de venda) passam a atualizar-se sozinhos.

Exemplo prático
---------------
Atributo "Tecido Premium": preco_por_m2=10, m2_da_peca=2, margem=1.5, margem_geral=1.2,
valor_do_corte=5 -> price_extra = 10*2*1.5*1.2 + 5 = 41.
Produto com custo fornecedor 100, x_studio_margem=1.5, x_studio_margem_2_2=1.2 ->
list_price = ceil(100*1.5*1.2) = 180.

FAQ / Resolução de problemas
----------------------------
- P: O preço de venda não é o que eu introduzi manualmente.
  R: Este módulo torna `list_price` CALCULADO; o valor manual é substituído pela fórmula.
     Para preços manuais, este comportamento tem de ser revisto/desligado.
- P: price_extra ficou 0.
  R: Só fica 0 se todos os fatores forem 0; confirmar m²/margens preenchidos.
- P: O preço arredonda sempre para cima.
  R: É intencional (math.ceil) para não vender abaixo do custo+margem.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- ALTERAÇÃO ESTRUTURAL: `list_price` passa a ser um campo calculado/armazenado — afeta toda
  a precificação standard do Odoo. Avaliar impacto antes de instalar em produção.
- Depende de campos Studio de margem no produto.
""",
    "data": [
        "views/product_attribute_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
