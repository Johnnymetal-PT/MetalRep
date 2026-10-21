# -*- coding: utf-8 -*-

{
    "name": "PG Website Product Variant Description",
    "version": "17.0.1.0",
    'author':'Bytesfuel',
    'website':'https://bytesfuel.com/',
    "category": "eCommerce",
    "summary": "Descrição própria por variante de produto, mostrada na loja online e disponível em vendas/compras",
    "description": """
PG Website Product Variant Description
======================================

Origem
------
Módulo de terceiros (Bytesfuel). Integrado no projeto com prefixo pg_.

Objetivo de negócio
-------------------
Cada variante de produto pode ter uma descrição própria (não só o template), que é
apresentada ao cliente na loja online quando ele seleciona a variante, e fica também
disponível nas linhas de venda e de compra.

Pré-requisitos
--------------
- Módulos: `website_sale`.
- Preencher a "Variant Description" (`product_variant_desc`) em cada variante (product.product).

Como funciona
-------------
- `product.product`: campo `product_variant_desc` (Text, traduzível).
- `sale.order.line` e `purchase.order.line`: campo `product_variant_desc` relacionado
  (related, só leitura), para consulta nos documentos.
- Controller: faz override de `get_combination_info_website` para incluir a descrição da
  variante na resposta usada pela loja (combination info).
- Frontend (static/src/js/mixin.js): mostra/atualiza a descrição quando se muda de variante.

Passo a passo de utilização
---------------------------
1. Na variante do produto, preencher o campo "Variant Description".
2. Publicar o produto na loja; ao escolher essa variante, o cliente vê a descrição própria.
3. (Opcional) Traduzir a descrição por idioma — o campo é traduzível.

Exemplo prático
---------------
Produto "Sofá" com variante "3 lugares - Azul": preencher a descrição da variante com as
medidas e composição específicas; o site passa a mostrá-las ao selecionar essa variante.

FAQ / Resolução de problemas
----------------------------
- P: A descrição não aparece no site.
  R: Confirmar que o campo está preenchido NA VARIANTE (product.product) e que a página foi recarregada.
- P: Como traduzo?
  R: O campo é traduzível; usar o mecanismo de traduções do Odoo.

Pontos de atenção
-----------------
- Módulo proprietário (OPL-1) de terceiros; atualizações do fornecedor podem sobrepor alterações.
- O override de `get_combination_info_website` depende da estrutura do `website_sale`.
""",
    "depends": ['website_sale'],
    'data': [
        'views/templates.xml',
        'views/product_variant_view.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            '/pg_product_variant_description_bytesfuel/static/src/js/mixin.js',
        ],
    },

    "images": ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'license': 'OPL-1',
    'price': 10.00,
    'currency': 'USD',
}
