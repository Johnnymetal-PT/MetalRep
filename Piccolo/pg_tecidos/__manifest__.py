# -*- coding: utf-8 -*-
{
    'name': 'PG Tecidos Customization',
    'version': '17.0.1.0.0',
    'summary': 'Logica MRP custom: ao criar uma MO, le a descricao das variantes (TECIDO, ACABAMENTO, ARO, etc.) da linha SO, duplica a BoM, aplica consumos do pg_price_table e duplica componentes "Tecido X" / "Polimento Y" para que cada MO use componentes distintos por encomenda.',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/pg_tecidos_view.xml',
    ],
    'description': """
PG Tecidos Customization
========================

a) Objetivo de negocio
----------------------
A Piccolo fabrica cadeiras/colchoes/sofas onde **cada encomenda tem
tecidos, acabamentos e cores especificos**. A BoM standard nao chega
porque cada SO acrescenta variantes textuais (ex.: "TECIDO: Linho
Bege"). Este modulo:
- Le a descricao da linha SO ao criar a MO.
- Duplica a BoM principal para essa MO.
- Substitui componentes generericos ("Tecido", "Acabamento", "Aro")
  por copias com o nome exato do tecido/acabamento escolhido.
- Aplica quantidades de consumo dinamicas (tabela em
  ``pg_price_table``) consoante o ``product_qty``.
- Cria/atualiza ``product.supplierinfo`` para que o procurement
  saiba a quem comprar.

b) Pre-requisitos
-----------------
- Modulos standard ``mrp``, ``stock``.
- Modulo ``pg_price_table`` instalado (campos ``price_1..price_10``
  no ``product.template`` para a tabela de consumo).
- Convencao na descricao da linha SO: cada atributo numa secao
  ``"TERMO: valor"`` separada por virgulas. Termos suportados:
  - ``TECIDO COSTAS FRENTE + ASSENTO``
  - ``TECIDO COSTAS TRAS``
  - ``TECIDO CIMA``
  - ``TECIDO BAIXO``
  - ``TECIDO``
  - ``ACABAMENTO`` / ``ACABAMENTO com Ponteira``
  - ``ARO``
  - ``ALTERACAO COR DOS PES``
- BoM principal do produto (a mais antiga - ``order='create_date asc'``)
  e a fonte; as suas linhas de "tecido"/"acabamento" sao genericas.
- Atributos do produto: ``DIMENSOES DO COLCHAO`` (opcional, lido das
  ``product_template_attribute_value_ids`` e injetado na descricao).
- Fornecedores ``-Fornecedor de tecidos a definir`` e ``Polidor C/Arte
  Mobiliario, Lda`` cadastrados em ``res.partner`` (matching por nome
  exato).

c) Como funciona
----------------
- ``models/mrp_production.py`` (override de ``create``):
  1. Se ``product_description_variants`` esta vazio, copia do
     ``sale.order.line.name`` correspondente.
  2. Extrai cada termo (case-insensitive ``find('TERMO:')``).
  3. Adiciona ``DIMENSOES DO COLCHAO`` lendo
     ``product_template_attribute_value_ids``.
  4. Re-monta ``product_description_variants`` como CSV de pares
     ``Termo: valor``.
  5. ``_search_oldest_bom``: procura a BoM mais antiga do template
     e classifica cada bom_line por termo (substring match no nome
     do produto componente, com prioridade para os mais especificos).
  6. ``_duplicate_bom``: ``bom.copy()``, escala
     ``product_qty * product_uom_qty`` e ``line.product_qty``
     **excepto** para componentes de termo (tecido*), porque vao ser
     recalculados em ``_apply_consumption_values``.
  7. ``_apply_consumption_values``: para cada bom_line de tecido, le
     ``price_N`` do componente (N = ``product_qty - 1``, capado a 10)
     e escreve ``line.product_qty = per_unit * product_qty``.
  8. ``_duplicate_and_assign_to_bom``: para cada termo com texto
     extraido:
     - Encontra ou cria um ``product.template`` "Tecido <X>" /
       "<Produto> <Acabamento>" / etc.
     - Reusa se existente; senao copia do componente generico,
       acrescenta os ``price_1..10`` via ``_copy_custom_fields`` e
       chama ``_assign_vendor_to_product``.
     - Substitui o ``line.product_id`` da BoM duplicada pelo novo
       produto.
  9. Cria a MO em ``state='draft'`` e atribui a BoM duplicada
     (``production.write({'bom_id': duplicated_bom.id})``).

- ``models/stock_move.py``:
  - Acrescenta ``partner_id`` (Fornecedor) ao ``stock.move``,
    computed do ``product.supplierinfo`` do template.
  - Override de ``write``: ao mudar ``partner_id`` no move,
    atualiza/cria ``product.supplierinfo`` para refletir.

- ``models/stock_rule.py``:
  - Override de ``_run_manufacture``: forca a MO criada a
    ``state='draft'`` (em vez de ``confirmed``) para que o utilizador
    possa abrir manualmente e confirmar.
  - Inclui mensagem ``message_post`` com a origem para rasto.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo (e ``pg_price_table`` se ainda nao estiver).
2. Preencher ``price_1..price_10`` nos componentes "Tecido X",
   "Aro Y", "Acabamento Z" no backoffice.
3. Garantir fornecedores genericos cadastrados.
4. Confirmar SO; ao gerar MO via procurement:
   - A descricao das linhas SO e parseada.
   - A BoM e duplicada e os componentes especificos sao criados.
5. Abrir a MO (state=draft); confirmar normalmente.

e) Exemplo pratico
------------------
SO ``S00200`` com 2 cadeiras "Modelo Y". Descricao da linha SO:
``"Modelo Y - TECIDO: Linho Bege, ACABAMENTO: Verniz Mate"``.
Ao gerar a MO:
- BoM original duplicada: ``MO/00250/BOM (copy)``.
- Componente generico "Tecido" substituido por "Tecido Linho Bege"
  (criado se nao existir, fornecedor "-Fornecedor de tecidos a
  definir").
- Componente generico "Acabamento" substituido por "Modelo Y Verniz
  Mate" (fornecedor "Polidor C/Arte Mobiliario, Lda").
- ``price_2`` do "Tecido Linho Bege" e usado como consumo por
  unidade -> total = ``price_2 * 2``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"MO sem componentes especificos"* -> descricao da linha SO nao
  segue o formato ``TERMO: valor`` (separadores em falta) ou termos
  com typos.
- *"Tecido duplicado varias vezes"* -> ``_duplicate_and_assign_to_bom``
  desativa duplicados antigos via
  ``existing_product[1:].write({'active': False})``. Se aparecem
  cuplicados, validar manualmente em ``product.template`` filtros
  inactive.
- *"Vendor nao atribuido"* -> nome do fornecedor mudou; alinhar com
  os literais hardcoded no codigo (ver "Pontos de atencao").
- *"Consumo nao escala com qty"* -> ``price_N`` em falta no
  componente. Preencher tabela de consumo.

g) Pontos de atencao / avisos
-----------------------------
- **Termos HARDCODED com acentos** (case-insensitive mas literais):
  ``TECIDO COSTAS TRAS`` (com acento em "TRAS"), ``ALTERACAO COR DOS
  PES``, ``DIMENSOES DO COLCHAO``. Manter exatamente assim na
  descricao da SO.
- **Fornecedores HARDCODED por nome**:
  - ``-Fornecedor de tecidos a definir`` (note o ``-`` no inicio).
  - ``Polidor C/Arte Mobiliario, Lda``.
  Renomear estes partners parte a logica.
- **Risco de colisao** documentado no codigo
  (``_duplicate_and_assign_to_bom``): produtos com substring "aro"
  (ex.: ``CAROLINA``) eram apanhados pelo branch do termo "ARO".
  Decisao: usar SEMPRE o termo classificado em ``_search_oldest_bom``
  e nao re-classificar a partir do nome do produto duplicado.
- **Existing product reuse**: se ja existe ``product.template`` com
  o nome calculado, e reaproveitado; nao se cria novo. Implica que
  ``price_1..10`` reais sao os do produto reaproveitado, nao os do
  generico. Esta consistente desde que se carreguem os ``price_*``
  no primeiro reuso.
- **product_qty <= 1**: usa ``price_1``; ``>= 10`` usa ``price_10``;
  a tabela tem 10 linhas fixas.
- Indices da tabela: ``min(int(qty)-1, 9)`` - cuidado com qty
  fracionarios.
- A complexidade do override de ``create`` torna a MO MUITO mais
  lenta que a standard; aceitavel pela cardinalidade Piccolo.
""",
    'installable': True,
    'application': False,
}
