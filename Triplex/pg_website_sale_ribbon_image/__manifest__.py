{
    "name": "PG Website Sale Ribbon Image",
    "summary": "Distintivo de produto como imagem (selo), editavel pelo website builder",
    "description": """
PG Website Sale Ribbon Image
============================

Objetivo de negocio
-------------------
Os distintivos ("badges") standard do Odoo so aceitam texto com cor de fundo e cor de letra,
em forma de fitinha inclinada ou de etiqueta reta. A Casa Magna precisa de colocar sobre a
foto do produto um selo grafico (por exemplo o carimbo circular "NEW - NEW - NEW"), com fundo
transparente, e quer que seja a propria equipa do cliente a faze-lo pelo editor do website,
sem pedir desenvolvimento a cada campanha.

Este modulo acrescenta ao distintivo a possibilidade de ser uma imagem em vez de texto,
mantendo exatamente o mesmo gesto de utilizacao: no editor, clicar no produto, escolher o
distintivo, gravar.

Pre-requisitos
--------------
- Modulos: `website_sale`.
- Templates standard `website_sale.products_item` e `website_sale.shop_product_image`
  presentes (e onde o distintivo e desenhado).

Como funciona
-------------
Nao tem codigo Python nem altera o modelo `product.ribbon`.

O campo `product.ribbon.html` e um campo HTML sem sanitizacao e os templates da loja
imprimem-no em bruto (`t-out`). O modulo aproveita isso: quando se escolhe uma imagem, o
editor coloca um `<img>` dentro do distintivo e o mecanismo de gravacao standard do Odoo
(`_saveRibbon`) persiste-o, tal como ja persistia o texto. As classes CSS aplicadas ao
distintivo sao guardadas no campo `html_class`, tambem pelo mecanismo standard.

Consequencia importante: nenhum template QWeb e herdado. O selo aparece em todo o lado onde
o Odoo ja desenha o distintivo (grelha da loja e pagina de produto), inclusive em sites que
tenham copias proprias dos templates (vistas COW por website), sem risco de a heranca nao ser
aplicada.

Componentes:
- `static/src/js/ribbon_image_option.js`: estende a opcao `WebsiteSaleProductsItem` do editor
  com "Imagem" (abre o seletor de media), "Remover imagem" e "Tamanho do selo"; esconde as
  opcoes que nao fazem sentido num selo (texto, cores, forma) e corrige a pre-visualizacao na
  lista de distintivos, que de outro modo mostraria o HTML como texto.
- `views/snippet_options.xml`: acrescenta esses botoes ao painel do editor e da nome as
  opcoes standard que passam a poder ser escondidas.
- `static/src/scss/ribbon_image.scss`: estilo do selo no site (fundo transparente, sem
  rotacao, colado ao canto da foto, tres tamanhos).
- `static/src/scss/ribbon_image_editor.scss`: miniatura do selo na lista de distintivos do
  painel do editor.

Passo a passo de utilizacao
---------------------------
1. Abrir a loja (`/shop`) e clicar em "Editar".
2. Clicar no cartao do produto. No painel da direita, seccao "Product", opcao "Distintivo".
3. Escolher um distintivo existente ou criar um novo com o "+".
4. Clicar no lapis para entrar em modo de edicao do distintivo.
5. Em "Imagem", escolher ou carregar o ficheiro do selo (PNG com fundo transparente).
6. Ajustar "Tamanho do selo" (Pequeno / Medio / Grande) e "Position" (esquerda / direita).
7. Gravar. Para os restantes produtos basta escolher o mesmo distintivo na lista.

Exemplo pratico
---------------
Criar o distintivo "NEW" com o carimbo circular da marca, tamanho Medio, a direita.
Aplica-lo as novidades da colecao. Quando deixarem de ser novidade, por o distintivo a
"Nenhum(a)" em cada produto; o selo continua disponivel para a campanha seguinte.

FAQ / Resolucao de problemas
----------------------------
- P: Alterei a imagem de um distintivo e ela mudou noutros produtos.
  R: E o comportamento normal do Odoo: o distintivo e um registo partilhado. Para um selo
     diferente, criar um novo distintivo com o "+" em vez de editar o existente.
- P: O selo nao aparece nos produtos que estao na homepage.
  R: Os blocos dinamicos de produtos e os cartoes montados a mao nao desenham o distintivo do
     produto (e assim no Odoo standard). O selo aparece na loja e na pagina do produto.
     Mostrar o selo nos blocos dinamicos exige trabalho adicional.
- P: A imagem aparece esticada ou demasiado grande.
  R: Usar um PNG quadrado com fundo transparente e ajustar em "Tamanho do selo".
- P: Escolhi uma imagem mas continuo a ver a caixa de texto do distintivo.
  R: Confirmar que o modulo esta instalado e limpar a cache do browser; os assets do editor
     sao carregados num bundle proprio (`website.assets_wysiwyg`).

Pontos de atencao
-----------------
- Depende de `product.ribbon.html` continuar a ser um campo HTML sem sanitizacao e de os
  templates continuarem a imprimi-lo com `t-out`. Uma atualizacao major do Odoo obriga a
  revalidar este pressuposto.
- A imagem do selo fica guardada como anexo (`ir.attachment`) e referenciada por URL dentro do
  campo `html` do distintivo. A ferramenta "imagens nao utilizadas" do website pode lista-la
  como nao usada, porque nao esta referenciada em nenhuma vista; nao a apagar.
- O selo herda `pointer-events: none` do distintivo standard, pelo que nunca intercepta o
  clique no produto.
""",
    "version": "17.0.1.0.0",
    "category": "Website/eCommerce",
    "author": "Parametro Global",
    "depends": ["website_sale"],
    "data": [
        "views/snippet_options.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pg_website_sale_ribbon_image/static/src/scss/ribbon_image.scss",
        ],
        "website.assets_wysiwyg": [
            "pg_website_sale_ribbon_image/static/src/js/ribbon_image_option.js",
            "pg_website_sale_ribbon_image/static/src/scss/ribbon_image_editor.scss",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
