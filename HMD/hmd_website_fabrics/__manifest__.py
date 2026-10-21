# -*- coding: utf-8 -*-
{
    'name': 'HMD Website Fabrics',
    'version': '18.0.1.2.0',
    'summary': 'Pagina de detalhe por tecido, agrupamento por familia e composicao do tecido.',
    'description': """
HMD Website Fabrics
===================

a) Objetivo de negocio
----------------------
Na pagina /fabrics a HMD quer que cada amostra seja clicavel e leve a uma
pagina com as especificacoes daquele tecido: categoria, composicao basica e
descarga da ficha tecnica. Pedido de 27/08/2026, modelacao decidida a
07/09/2026.

Decisoes da HMD, para nao serem re-discutidas:
  - um tecido e um `product.template` (a serie, ex. LUDE) e cada cor e uma
    variante `product.product` com a sua fotografia. Sao elas que carregam os
    produtos, por isso o modelo segue o que elas ja fazem;
  - as especificacoes sao da SERIE, nao da cor. Por cor seriam ~250 fichas em
    vez de 32;
  - a pagina agrupa os tecidos por CATEGORIA de gama (CAT I a CAT V e
    C.O.M.), que e o que o cliente escolhe na pagina do movel. A familia
    (LU, AL, IM...) continua a existir, mas so como informacao;
  - o que aparece no site e curado pelo campo `Publicado` de cada tecido, que
    ja existe e que elas ja sabem usar. Nao ha campo novo de curadoria.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo standard `website_sale`.
- Uma categoria publica de tecidos. Por omissao procura-se pelo nome
  "Tecidos"; o nome e configuravel no parametro de sistema
  `hmd_website_fabrics.category_name`.

c) Como funciona (tecnico)
--------------------------
1. `product.template` (`models/product_template.py`):

   - `hmd_fabric_composition`: Text. A composicao basica, por serie.
   - `hmd_fabric_care_image`: Image. As instrucoes de limpeza, por serie
     (tarefa #7542, 24/09/2026).
   - `_hmd_fabric_spec_items()`: as linhas de texto das especificacoes
     (Category = gama CAT, Composition). Uma so fonte para a pagina do tecido e para a
     seccao "Specifications" da pagina de produto.
   - `hmd_fabric_family`: Char calculado e ARMAZENADO, com as duas primeiras
     letras do nome em maiusculas. E o agrupador da pagina.
   - `hmd_fabric_category`: Selection com CAT I a CAT V e C.O.M. E o que
     divide as seccoes da pagina /fabrics.
   - `_hmd_fabric_categories()`: devolve [(chave, titulo, ancora, recordset)]
     pela ordem do campo, so com tecidos publicados e classificados. E o que a
     vista do tema consome, para o agrupamento nao viver em QWeb.
   - `_hmd_seed_fabric_categories()`: atribuicao inicial, so onde estiver
     vazio. Nunca escreve por cima do que a HMD ajustar.
   - `_hmd_is_fabric()`: se o produto esta na arvore da categoria de tecidos.

2. `product.public.category` (`models/product_public_category.py`):

   - `_hmd_fabrics_root()`: resolve a categoria raiz dos tecidos pelo nome
     configuravel. Uma so via de resolucao, para nao haver duvida de onde vem.

3. Controller (`controllers/main.py`): rota
   `/fabrics/<model("product.template"):fabric>`, publica, com website. Devolve
   404 a quem nao esta publicado ou nao e tecido — sem isso a rota seria uma
   segunda pagina de produto para o catalogo todo.

4. Vistas (`views/`): a pagina de detalhe (`hmd_fabric_detail`), os campos
   do tecido no formulario do produto, num separador proprio, e o quadro
   "Fabric" na seccao "Specifications" da pagina de produto
   (`product_page_templates.xml`, so em tecidos).

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Confirmar que os tecidos estao na categoria publica "Tecidos".
3. Por tecido: escrever a composicao e carregar a imagem das instrucoes de
   limpeza no separador "Tecido", e anexar a ficha tecnica em Documentos com
   "Publicar no site" ligado.
4. Publicar ou despublicar cada tecido para decidir o que aparece em /fabrics.

e) Exemplo pratico
------------------
O LUDE tem 7 cores com fotografia. Em /fabrics aparece na familia "LU"; ao
clicar em qualquer das 7 amostras abre /fabrics/lude-<id>, com as 7 amostras,
a categoria, a composicao e o botao de descarga da ficha.

f) FAQ / Resolucao de problemas
-------------------------------
P: Um tecido nao aparece em nenhuma seccao. Porque?
R: Nao tem categoria atribuida. Sem categoria nao ha seccao onde o por.
Atribui-se no separador "Tecido" do produto.

P: A ficha tecnica nao aparece.
R: O documento tem de estar em `product.document` no proprio tecido, ativo e
com `shown_on_product_page`. A descarga usa a rota do website_sale
`/shop/<slug>/document/<id>`, que valida isso tudo — nao ha rota nossa.

P: Um tecido nao aparece em /fabrics de todo.
R: Ou nao esta publicado, ou nao esta na arvore da categoria de tecidos.

g) Pontos de atencao / avisos
-----------------------------
- `hmd_fabric_family` sai das duas primeiras letras do nome. E a convencao que
  a HMD usa hoje (LUDE/LUCO, ALBO/ALRC, IMAI/IMAN, SYAT/SYBO, JQNI). Se um dia
  deixar de ser, um tecido cai numa familia errada em vez de dar erro — degrada,
  nao parte. A saida duradoura sao as subcategorias descritas na FAQ.
- A rota nao substitui `/shop`: um tecido continua a ter pagina de produto.
  Esta e uma segunda vista do mesmo registo, sem preco nem carrinho.
""",
    'category': 'Website',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'website_sale_comparison'],
    'data': [
        'views/product_views.xml',
        'views/fabric_templates.xml',
        'views/product_page_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hmd_website_fabrics/static/src/scss/fabric_specs.scss',
        ],
    },
    'installable': True,
    'application': False,
}
