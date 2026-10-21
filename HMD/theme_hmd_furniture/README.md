# HMD Furniture — tema do website

Implementa o desenho aprovado da Mónica Hedderich (Adobe XD, Agosto 2026)
para o website da HMD Furniture.

## Origem do desenho

Ficheiros em `Website_Design/` na raiz do repositório:

| Ficheiro | Conteúdo |
|---|---|
| `Desktop/SVG/*.svg` | 8 páginas @1920px, com texto real e imagens embebidas |
| `Desktop/PDF/*.pdf` | as mesmas 8 páginas, para revisão visual |
| `Mobile/*.svg` | 5 ecrãs @393px (Home, Grelha, Produto, Menu, Submenu) |

Os SVG são a **fonte de verdade** das medidas: os valores em
`static/src/scss/tokens.scss` foram extraídos deles e não devem ser alterados
sem validar contra o original.

## Sistema de design

* **Prata** — títulos (80 / 89 / 54 / 33 px)
* **Courier New** — navegação e corpo editorial (14–30 px)
* **Inter** — interface e rodapé (8–20 px)
* Tinta `#1F1C1C` / `#222120`, cinza `#EDEDED`, destaque `#F80000`,
  amostras `#624C1B` e `#D9A32A`

## Estrutura

```
models/theme_utils.py  gancho _post_copy: desliga cabeçalho e rodapé nativos
views/layout.xml       barra de topo, cabeçalho com mega-menu, rodapé
views/pages.xml        Home, We are, Portfolio, Collection, Fabrics, Materials, Contact
views/shop.xml         página de produto e grelha de catálogo (e-commerce)
```

## Cabeçalho e rodapé: porque existe o `_post_copy`

O cabeçalho e o rodapé do desenho substituem os mesmos nós que os templates
nativos do Odoo — `//header//nav` e `//div[@id='footer']`. Com os nativos
activos há dois `position="replace"` sobre o mesmo nó, o segundo não encontra
o nó, e **todas as páginas do site devolvem HTTP 500**.

O Odoo trata cabeçalhos e rodapés como conjuntos mutuamente exclusivos
(`theme.utils._header_templates` / `_footer_templates`). Como os nossos não
pertencem a esses conjuntos, `_theme_hmd_furniture_post_copy()` desliga todos
os nativos quando o tema é aplicado.

> **Limitação conhecida.** Se alguém escolher outro cabeçalho ou rodapé nas
> opções do construtor de website, o Odoo reactiva um dos nativos e o erro 500
> volta. Neste site o cabeçalho e o rodapé são do tema e não devem ser trocados
> por aí. Para repor: desactivar `website.template_header_default` e
> `website.footer_custom` nas vistas do website.

## Menus

`theme.website.menu._convert_to_base_model` copia o campo `url` tal e qual e
**não** o deriva do `page_id` — um menu só com `page_id` fica com `href` vazio.
Por isso todos os menus do tema trazem `url` explícito.

O tema também não cria `Home` nem `Contact us`: o Odoo já os cria em qualquer
website novo, e duplicá-los enche a navegação. O `Shop` e o `Blog` que o Odoo
cria por defeito não constam do desenho e são retirados na configuração do
site (o `Products` do desenho vive na coluna direita e aponta para `/shop`).

## Decisão de arquitectura no e-commerce

A página de produto **não** reescreve o formulário do `website_sale`. As
secções do desenho são acrescentadas nos ganchos `oe_structure` nativos e o
aspecto é obtido por CSS sobre a marcação existente. Reescrever o formulário
partiria o JavaScript de variantes, carrinho e wishlist do Odoo.

Os downloads ("technical sheet", "3D files") usam `product.document` com
*Publish on website* — a HMD gere os ficheiros pelo backoffice.

## Instalação

Requer deploy para a pasta de addons do servidor e depois:

```
odoo-bin -c <conf> -d HMD -i theme_hmd_furniture --stop-after-init
```

Aplicar ao website pretendido em *Website → Configuração → Website → Tema*.

## Feedback da Mónica de 18/09/2026

Nove PDFs anotados sobre a versão que estava no ar a 18/09, na pasta `tarefa/`
na raiz do repositório. O que mudou no tema por causa deles está nos commits
de 21/09; o que ficou por fazer está listado abaixo.

Duas decisões que não são código e vivem no backoffice:

* **Aviso «This product has no valid combination».** É do Odoo e diz a verdade:
  o produto não tem combinação válida. Não se esconde — corrige-se o produto.
  Medido a 22/09/2026: a causa não são as exclusões de atributos (nenhum
  modelo fica sem combinação por causa delas), é `sale_ok = False` num produto
  publicado — em produção, só o `RODAPE P/BISTRO 850x560` (id 24986).
* **Referência a projeto por baixo de COMPARE.** É uma etiqueta de produto
  (`product.tag`, ex. SOFITEL MALABO). **Resolvido no tema a 23/09/2026**, não
  nos dados: `shop.scss` esconde o bloco de etiquetas na página de produto.
  Desmarcar **Visível no eCommerce** nas etiquetas chegou a ser feito em teste e
  foi revertido: a marca é da base toda e desligava também, no site actual, os
  68 links de etiqueta para a página do projeto (`hmd_product_tag_project_link`).
  Sai o bloco inteiro porque o desenho do bloco de compra não tem etiquetas.

## Pendente

* Tradução PT das categorias do mega-menu (o desenho está em PT, o catálogo em EN)
* Substituir as imagens de demonstração por fotografia real do catálogo
* Texto definitivo das páginas `/private` e `/professional` — existem desde
  17/09/2026, mas com as palavras do bloco B2B da página de produto como
  provisório, por rever pela HMD. **Desde 21/09 já não têm entrada no
  cabeçalho** (feedback da Mónica); continuam acessíveis por URL.
* Confirmar se os produtos têm documentos 2D/3D anexados. O bloco
  `#product_documents` já os mostra no fim do bloco de compra — o que falta,
  se faltar, são os ficheiros, não o código.
* Posição do logótipo: a prancha «MENU LADO DIREITO» mostra-o à esquerda da
  coluna de atalhos, e não por cima dela como está. Por confirmar.
* Cabeçalho mobile: o desenho de Agosto punha conta/carrinho/wishlist e
  pesquisa na primeira linha. Com os widgets na barra de topo, a pesquisa
  passou a acompanhar o logótipo e o MENU. O feedback é todo de ecrã grande e
  não cobre isto.
