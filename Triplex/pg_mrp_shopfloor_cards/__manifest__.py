{
    "name": "PG MRP Shop Floor Cards",
    "summary": "Cartões do Shop Floor com origem, leitura por código de barras e pré-visualização de PDF/imagem",
    "version": "17.0.1.1.0",
    "category": "Manufacturing",
    "description": """
PG MRP Shop Floor Cards
=======================

Objetivo de negócio
-------------------
Dar ao operador do chão de fábrica (Shop Floor do MRP) acesso rápido, no próprio cartão
da ordem de fabrico, à origem do trabalho e aos documentos de apoio (ficha em PDF e
imagem do estofo), e permitir localizar a ordem lendo um código de barras.

Origem da imagem (alterado a 28/07/2026)
---------------------------------------
A imagem do cartão tem três origens, resolvidas por precedência no campo calculado
`mrp.production.pg_card_image_url` (`models/mrp_production.py`):

1. `x_studio_imagem_estofo` da ordem de fabrico — excepção manual, para quando alguém quer
   uma imagem específica naquela ordem;
2. `x_studio_foto` da **linha de venda** de origem — é o caso dos produtos especiais criados
   na hora ao preencher a encomenda, em que ninguém carrega imagem na ficha do produto e a
   imagem é posta diretamente na linha;
3. `image_1920` do produto — a imagem de catálogo, o caso normal.

Até esta alteração o cartão lia apenas o campo Studio da ordem, de preenchimento manual.
Medido em `triplex_test`: estava vazio em **199 de 200** ordens de fabrico abertas. Era esta
a causa de não aparecer imagem no chão de fábrica, incluindo nas ordens abertas em frente ao
cliente na reunião de 27/07/2026 (ponto A6 / tarefa T7).

Não havia nada avariado: **nunca existiu ligação**. Convém não confundir os dois campos de
imagem da linha de venda:

- `x_studio_related_field_5cq_1jiv8p6e1` ("Imagem") é `related` a `product_id.image_1920`,
  não armazenado e readonly — é uma janela para a imagem do produto e não guarda nada;
- `x_studio_foto` ("Foto") é um binário armazenado e editável — **é aqui** que a imagem dos
  produtos especiais é carregada.

Porque é resolvido no servidor
------------------------------
A origem 2 exige chegar da ordem de fabrico à linha de venda. O caminho é
`move_finished_ids.move_dest_ids.sale_line_id` — note-se que o `move_finished_ids.sale_line_id`
vem **vazio** nestas ordens, é pelo destino do movimento que se chega lá. Fazer esse percurso
no browser custaria várias chamadas por cartão; assim o cliente lê um campo e recebe o
endereço pronto.

A presença de cada imagem é verificada com o contexto `bin_size`, que faz o Odoo devolver a
dimensão do ficheiro em vez do ficheiro. Sem isso, verificar se existe imagem trazia a
imagem inteira do disco para o servidor só para a descartar, a multiplicar pelos cartões
no ecrã.

Pré-requisitos
--------------
- Módulos: `mrp_workorder` (app Shop Floor) e `web`.
- Campo Studio em `mrp.production`: `x_studio_ficheiro_pdf` (Binary, PDF), para o botão de
  PDF. O `x_studio_imagem_estofo` (Image) é opcional — sem ele, a imagem vem do produto.
- O Shop Floor é uma interface OWL no backend; este módulo é quase todo frontend (JS/XML/SCSS).

Como funciona
-------------
Patches OWL (não altera modelos Python, apenas o frontend):
- `mrp_display_action_patch.js`: acrescenta os campos `origin`, `x_studio_ficheiro_pdf` e
  `x_studio_imagem_estofo` aos dados carregados para cada ordem.
- `mrp_display_record_patch.js`: adiciona ao cartão os botões "PDF Preview" e "Image
  Preview" (visíveis só se o respetivo ficheiro existir; o estado é lido/cacheado por ordem).
- `preview_dialog.js` + `preview_dialog.xml`: janela de pré-visualização com zoom (imagem)
  ou incorporação do PDF.
- `mrp_display_patch.js`: ao ler um código de barras, procura pela `origin` (ou `name`),
  facilitando localizar a ordem a partir da etiqueta.
- `views/mrp_production_search_views.xml`: ajustes à pesquisa de ordens de fabrico.

Passo a passo de utilização
---------------------------
1. Preencher nas ordens de fabrico os campos Studio com o PDF da ficha e/ou a imagem do estofo.
2. Abrir a app Shop Floor (Chão de Fábrica) e localizar a ordem (lista ou leitura de código de barras).
3. No cartão, carregar em "PDF Preview" ou "Image Preview" para ver o documento sem sair do ecrã.
4. Usar zoom (botões ou Ctrl+scroll na imagem) para inspecionar o detalhe.

Exemplo prático
---------------
Operador lê o código de barras da folha de produção -> o Shop Floor filtra pela origem e
mostra a ordem; ele abre a "Image Preview" para confirmar o tecido/estofo a aplicar.

FAQ / Resolução de problemas
----------------------------
- P: Os botões de pré-visualização não aparecem.
  R: A ordem não tem `x_studio_ficheiro_pdf`/`x_studio_imagem_estofo` preenchidos, ou os
     campos Studio não existem nesta base de dados.
- P: A leitura de código de barras não filtra nada.
  R: É preciso que o código corresponda à `origin` (ou `name`) da ordem.
- P: Alterei o PDF e continua a mostrar o antigo.
  R: O estado é cacheado por ordem; reabrir a pré-visualização força nova leitura.

Pontos de atenção
-----------------
- Depende da estrutura interna do `mrp_workorder` (componentes MrpDisplay*); uma atualização
  major do Odoo pode quebrar os patches e exigir revisão.
""",
    # `sale_stock` é indispensável: é ele que define `stock.move.sale_line_id`
    # (`sale_stock/models/stock.py:17`), o campo que liga a ordem de fabrico à linha de
    # venda de onde vem a foto dos produtos especiais. Sem esta dependência declarada, o
    # `pg_card_image_url` era carregado antes do `sale_stock` e o arranque do registry
    # falhava com "Dependency field 'sale_line_id' not found in model stock.move".
    "depends": ["mrp_workorder", "web", "sale_stock"],
    "data": [
        "views/mrp_production_search_views.xml",
        "views/mrp_display_action.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_cards/static/src/js/preview_dialog.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_patch.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_record_patch.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_sort_patch.js",
            "pg_mrp_shopfloor_cards/static/src/xml/preview_dialog.xml",
            "pg_mrp_shopfloor_cards/static/src/xml/mrp_display_record.xml",
            "pg_mrp_shopfloor_cards/static/src/scss/mrp_display_record.scss"
        ]
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False
}
