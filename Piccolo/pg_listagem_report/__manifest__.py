# -*- coding: utf-8 -*-
{
    'name': 'PG Listagem Report Overrides',
    'version': '17.0.4.2.2',
    'summary': 'Estende o report Listagem (stock.report_picking): adiciona a data do documento no topo, substitui a coluna 3 por Cubicagem (peso/volumes/cubicagem do move) e a coluna 4 por Material em Falta (mensagem de prontidao a partir do campo manual x_studio_pronto dos componentes da MO). Acrescenta a Listagem para Compras (report na List View da purchase.order: descricao, imagem, data da compra e cliente da encomenda, sem precos). Nos produtos especiais (cascos), cujo produto de catalogo nao tem foto, a coluna Imagem vai buscar a foto carregada na linha da encomenda de venda de origem (campo Studio x_studio_imagem_produto_especial).',
    'depends': ['stock', 'purchase', 'mrp', 'sale'],
    'data': [
        'views/res_partner_views.xml',
        'views/report_picking_grouped_inherit.xml',
        'report/listagem_compras_report.xml',
    ],
    'description': """
PG Listagem Report
==================

a) Objetivo de negocio
----------------------
O relatorio "Listagem" (variante interna do stock.report_picking) e
usado na Piccolo como ficha de bordo do operador da expedicao.
Este modulo:
- adiciona no topo da listagem a "Data do documento" (momento em que o
  documento e tirado/impresso);
- substitui a coluna 3 por "Cubicagem" (Peso / Volumes / Cubicagem por
  linha);
- substitui a coluna 4 por "Material em Falta", agora uma mensagem de
  prontidao controlada manualmente pelo cliente.

b) Pre-requisitos
-----------------
- Modulos standard ``stock``, ``purchase``, ``mrp``.
- Campos Studio ``x_studio_peso_kg_1``, ``x_studio_volumes_3``,
  ``x_studio_cubicagem_1`` no ``stock.move`` (preenchidos via
  ``pg_cubicagem_wizard``).
- Campo Studio booleano ``x_studio_pronto`` no ``stock.move``,
  preenchido manualmente nas linhas de componente (``move_raw_ids``)
  da MO.

c) Como funciona
----------------
- ``models/stock_move.py``:
  - ``_pg_listagem_get_mo()``: encontra a MO de origem do move por
    ``origin == move.origin`` e ``product_id == move.product_id``
    (ignora MOs canceladas; a mais recente em empate).
  - ``_pg_listagem_material_pronto()`` (para cada move do picking):
    devolve True quando **todas** as linhas de componente da MO
    (``move_raw_ids``) tem ``x_studio_pronto`` a True. Sem MO ou sem
    componentes -> False (tratado como "em falta").
  - ``_pg_listagem_material_falta_por_grupo()``: quando ha material em
    falta, lista os componentes em falta (``x_studio_pronto`` False)
    agrupados em TECIDO / ESTRUTURA / ACABAMENTO. A classificacao e pelo
    **fornecedor principal** do componente (``seller_ids``) e o campo
    ``res.partner.pg_componente_tipo`` desse fornecedor. Componentes cujo
    fornecedor nao tenha tipo (ou sem fornecedor) NAO sao listados.

- ``views/report_picking_grouped_inherit.xml``:
  - insere a "Data do documento" antes da tabela da listagem;
  - faz xpath as colunas 3 e 4 (header e corpo) da listagem;
  - sob "Esta Material em Falta", lista os componentes em falta por grupo.

- ``models/purchase_order.py`` (Listagem para Compras):
  - ``_pg_listagem_get_mos()`` / ``_pg_listagem_get_sale_orders()``:
    travessia PO -> MO (por procurement group ou ``origin``) -> SO, para
    o cliente no cabecalho de cada encomenda.
  - ``_pg_listagem_get_sale_lines()``: MO -> ``move_dest_ids`` ->
    ``sale_line_id``, a linha de venda que originou a producao.
  - ``_pg_listagem_line_images()``: imagem por linha da compra. Usa a
    foto do produto do catalogo e, quando esta nao existe (produtos
    especiais: "Produto Especial Estrutura", "ESTRUTURA ESPECIAL", ...),
    a foto do campo Studio ``x_studio_imagem_produto_especial`` da linha
    de venda de origem, reduzida a 256px. So a usa quando a origem tem
    **uma** foto: com varias nao ha como saber qual pertence a cada
    linha, e mostrar a errada ao fornecedor e pior do que nao mostrar.
    Dois cuidados na leitura de binarios, ambos com o mesmo sintoma
    ("This file could not be decoded as an image file", que aborta a
    impressao inteira):
    - ``image_process`` recebe e devolve **bytes crus**, nao base64: e
      preciso ``b64decode`` antes e ``b64encode`` depois (e o que o
      Odoo faz em ``fields.Image._image_process``);
    - ler com ``bin_size=False``, porque com ``bin_size`` no contexto
      (o cliente web poe-no ao listar registos) um campo binario
      devolve o **tamanho** do ficheiro, "98.02 Kb", em vez do
      conteudo.
    Ficheiros que nao sejam imagem sao ignorados com aviso no log, para
    nunca bloquearem a impressao.

- ``models/res_partner.py``:
  - ``res.partner.pg_componente_tipo`` (Casco/Tecido/Polimento): voltou a
    ser usado pelo report para **agrupar** os componentes em falta.
    Mapeamento no report: Casco -> ESTRUTURA, Tecido -> TECIDO,
    Polimento -> ACABAMENTO.

d) Passo a passo de utilizacao
------------------------------
1. Instalar/atualizar o modulo.
2. Garantir que ``pg_cubicagem_wizard`` preencheu os campos
   ``x_studio_*`` de cubicagem dos moves.
3. Nas linhas de componente da MO, marcar manualmente ``x_studio_pronto``
   a medida que o material vai ficando pronto.
4. Imprimir o relatorio Listagem do picking - topo mostra a data do
   documento; coluna 3 a cubicagem; coluna 4 a mensagem de prontidao.

e) Mensagem da coluna "Material em Falta"
-----------------------------------------
- Todas as linhas de componente da MO com ``x_studio_pronto`` = True
  -> "O Material está Pronto" (verde).
- Caso contrario -> "Está Material em Falta" (vermelho).

f) Pontos de atencao / avisos
-----------------------------
- Match MO-Picking por ``origin`` + ``product_id``: se o nome do
  produto for muito generico e houver varias MOs com o mesmo nome,
  pode atingir a errada. Usar campo ``origin`` consistentemente.
- Se a MO de origem nao for encontrada, a linha aparece como "Está
  Material em Falta" (estado conservador, exige validacao manual).
- Listagem para Compras: a foto do produto especial so aparece se o
  comercial a tiver carregado no campo "Imagem Produto Especial" da
  linha da encomenda de venda. Sem foto na venda, a coluna sai vazia -
  nao ha outra origem para a imagem daquele artigo.
- Produtos de catalogo sem foto (ex.: tecidos, cadeiras standard sem
  imagem carregada) continuam a sair sem imagem: e falta de dados no
  produto, nao do report.
""",
    'installable': True,
    'application': False,
}
