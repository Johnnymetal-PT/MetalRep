# -*- coding: utf-8 -*-
{
    'name': 'PG Variant Specific Pricing',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Importa precos por variante (Excel) e force o lst_price da variante no /shop ignorando price_extra dos PTAVs.',
    'description': """
PG Variant Specific Pricing
===========================

a) Objetivo de negocio
----------------------
Cada variante na Piccolo pode ter preco proprio (negociado, promocao
ou tabela B2B) **independentemente** dos ``price_extra`` dos PTAVs.
Este modulo:
- Importa ``lst_price`` por variante de um Excel.
- Forca o /shop a mostrar ``lst_price`` da variante em vez de
  ``price + price_extra`` (override do ``_get_combination_info``).

b) Pre-requisitos
-----------------
- Modulos standard ``base``, ``product``, ``website_sale``.
- Bibliotecas Python: ``pandas`` + ``openpyxl``.
- Excel com colunas:
  - ``id`` -> external id da variante (ex.: ``__export__.product_product_42_abc``)
  - ``lst_price`` -> preco da variante.

c) Como funciona
----------------
- ``models/import_pricelist.py``:
  - ``pricelist.import.wizard`` (TransientModel) recebe ficheiro e
    itera. Para cada linha:
    1. Resolve ``ir.model.data._xmlid_to_res_model_res_id(external_id)``
       -> (model, res_id).
    2. So aceita ``product.product`` (variant); ignora outros.
    3. Faz ``write({'lst_price': ..., 'price_extra': 0.0})``.
  - ``ProductTemplate.action_import_pricelist`` e
    ``ProductProduct.action_import_pricelist``: botoes que abrem o
    wizard.

- ``ProductProduct``:
  - ``lst_price`` declarado como Float store=True (override do
    standard, que e computed). Permite escrever direto e
    persistir.
  - Override de ``create``/``write`` (verbose log, sem mudanca de
    semantica).
  - Override de ``_get_combination_info`` em ``ProductTemplate``
    (nota: definido dentro de ProductProduct mas decorado como
    @api.model, opera na realidade no template via super()):
    1. Chama super() para obter o combination_info standard.
    2. Sobrescreve ``price = product.lst_price`` e
       ``price_without_discount = product.lst_price``.
    3. ``price_extra = 0`` para anular contribuicao do PTAV.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Preparar Excel com colunas ``id`` (external id) e ``lst_price``.
   Tipicamente exportar via Settings > Technical > External
   Identifiers para variantes.
3. Botao "Importar Pricelist" (no template ou variante).
4. Upload do Excel.
5. No /shop, as variantes mostram o preco lst_price.

e) Exemplo pratico
------------------
Excel:
- ``id = __export__.product_product_42_abc``
- ``lst_price = 199.99``

Resultado:
- ``product.product`` 42 ganha ``lst_price = 199.99``,
  ``price_extra = 0``.
- No /shop, ao escolher variante 42 -> preco 199.99 (ignora os
  ``price_extra`` dos seus atributos).

f) FAQ / Resolucao de problemas
-------------------------------
- *"Preco da variante nao se reflete no /shop"* -> verificar que o
  override ``_get_combination_info`` esta a correr (logs verbose
  no ficheiro). Outra customizacao pode estar a sobrepor.
- *"External id nao encontrado"* -> Excel tem id mal formado ou
  variantes foram apagadas.
- *"Erro escrever lst_price"* -> ``lst_price`` originalmente
  computed; este modulo torna-o stored. Confirmar que nao ha
  conflito com outros modulos que tambem o redeclaram.

g) Pontos de atencao / avisos
-----------------------------
- ``_get_combination_info`` esta declarado dentro da classe
  ``ProductProduct``, com ``@api.model`` e chama
  ``super(ProductTemplate, self)``. O override aplica-se ao
  ``product.template`` (parent class). Aspeto pouco convencional;
  validar antes de refactor.
- O override forca ``price_extra = 0`` no combination_info -
  intencional para nao somar o extra do PTAV. Se mais tarde se
  quiser somar, remover essa linha.
- Re-declarar ``lst_price`` como ``store=True`` muda comportamento
  global de TODOS os ``product.product``. Outras customizacoes que
  dependam de ``lst_price`` computed podem partir.
- O wizard NAO valida que o external id e mesmo ``product.product``
  alem do check explicito - tudo o resto e silenciosamente ignorado.
""",
    'depends': ['base', 'product', 'website_sale'],
    'data': [
        'views/import_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
