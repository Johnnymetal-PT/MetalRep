{
    "name": "Hide Product Price Snippets",
    "summary": "Marca os preços do website como não-indexáveis para evitar rich snippets de preço no Google",
    "description": """
Hide Product Price Snippets
===========================

Objetivo de negócio
-------------------
Evitar que os motores de busca (Google) mostrem o preço dos produtos nos resultados
("rich snippets"), mantendo o preço visível na própria página da loja.

Pré-requisitos
--------------
- Módulos: `website_sale`.
- Templates standard `website_sale.product_price`, `website_sale.product` e
  `website_sale.badge_extra_price` presentes (versão Odoo coerente).

Como funciona
-------------
Não tem código Python — apenas herança de templates QWeb em views/website_sale_templates.xml:
- `website_sale.product_price`: reescreve o bloco de preço acrescentando o atributo
  `data-nosnippet="true"` (sinal para o Google não indexar aquele conteúdo), preservando o
  resto da apresentação standard do preço.
- `website_sale.product`: remove o atributo `data-product-tracking-info` do detalhe do produto.
- `website_sale.badge_extra_price`: marca o badge de preço extra também como `data-nosnippet`.

Passo a passo de utilização
---------------------------
1. Instalar o módulo.
2. Limpar a cache do website (Definições > Técnico > Limpar cache) e/ou reabrir a página.
3. Confirmar no HTML que o bloco de preço tem `data-nosnippet="true"`.
4. Aguardar o próximo crawl do Google; rich snippets de preço deixam de aparecer.

Exemplo prático
---------------
Antes: Google podia mostrar "Sofá X — 1.250,00 € — Triplex" nos resultados.
Depois: passa a mostrar apenas o título e a descrição normal, sem o preço destacado.

FAQ / Resolução de problemas
----------------------------
- P: O Google continua a mostrar o preço.
  R: As alterações nos rich snippets podem demorar dias a refletir-se nos resultados; usar
     o "URL Inspection" do Google Search Console para forçar a reindexação.
- P: O preço deixou de aparecer no site.
  R: O atributo `data-nosnippet` afeta apenas indexação; se o preço sumiu, é outra causa.
- P: Quero também esconder o preço dentro do site para utilizadores não logados.
  R: Este módulo não faz isso; é só para os snippets de pesquisa. Usar regras de acesso/Studio.

Pontos de atenção
-----------------
- Depende da estrutura dos templates standard do `website_sale`; uma atualização major do
  Odoo pode mudar os xpaths e exigir revisão.
- Não tem nenhum efeito em motores que não respeitem `data-nosnippet`.
""",
    "version": "17.0.1.0.0",
    "category": "Website/eCommerce",
    "depends": ["website_sale"],
    "data": [
        "views/website_sale_templates.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}

