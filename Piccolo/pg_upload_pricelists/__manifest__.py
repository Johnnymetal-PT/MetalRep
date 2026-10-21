# -*- coding: utf-8 -*-
{
    'name': 'PG Pricelist Import Module',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Importa pricelists e items de pricelist de um Excel: cada linha gera/atualiza uma pricelist + items por variante (mapeados por id externo do template e XML id das variantes).',
    'description': """
PG Upload Pricelists
====================

a) Objetivo de negocio
----------------------
Carregar tabelas de precos extensas a partir de um Excel sem ter de
criar cada item manualmente. Cada linha do Excel define uma
pricelist + um produto + um conjunto de variantes + ``fixed_price``.

b) Pre-requisitos
-----------------
- Modulos standard ``base``, ``product``.
- Bibliotecas Python: ``pandas`` e ``openpyxl``.
- Excel com colunas:
  - ``name`` -> nome da pricelist a criar/atualizar.
  - ``item_ids/product_tmpl_id`` -> external id do template
    (split por ``_`` e ``int(last)`` para extrair o id).
  - ``item_ids/product_id`` -> lista CSV de ids de variant
    (``product_template_attribute_value_id``).
  - ``item_ids/fixed_price`` -> preco fixo.

c) Como funciona
----------------
- ``models/pricelists_import.py``:
  - ``pricelist.import.wizard`` (TransientModel): receber ficheiro,
    parsear, criar pricelist + items.
  - ``import_pricelist``:
    1. ``pd.read_excel`` -> DataFrame.
    2. Para cada linha: ``product.pricelist.create({...})``.
    3. Resolve template via ``id == int(split('_')[-1])``.
    4. Para cada variant_id na CSV: encontra ``product.product``
       cujo ``product_template_variant_value_ids`` contem o id da
       variante - cria ``product.pricelist.item`` com ``fixed_price``.
  - ``Pricelist.action_import_pricelist``: abre o wizard.

d) Passo a passo de utilizacao
------------------------------
1. Instalar (garantir pandas + openpyxl).
2. Preparar Excel com as 4 colunas (ver pre-requisitos).
3. Vendas > Pricelists > botao "Importar Pricelist".
4. Upload do ficheiro - cada linha gera uma pricelist nova.

e) Exemplo pratico
------------------
Linha do Excel:
``name = "Pricelist 2026 Linho"; item_ids/product_tmpl_id =
"__export__.product_template_15_abc"; item_ids/product_id =
"__export__.product_attribute_value_42";
item_ids/fixed_price = 250.0``

Resultado:
- ``product.pricelist`` "Pricelist 2026 Linho" criada.
- 1 item: variante 42 do template 15 a 250 EUR.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Product template not found"* -> external id passado nao corresponde
  a nenhum template. Conferir export id ou usar id direto.
- *"Variant not found"* -> a CSV de variantes contem ids que nao
  pertencem ao template indicado, ou a variante nao foi gerada.
- *"Cria sempre nova pricelist"* -> o wizard NAO procura pricelist
  existente; cria sempre. Para atualizar in-place, modificar
  ``pricelist.create`` para ``search_or_create``.

g) Pontos de atencao / avisos
-----------------------------
- O wizard CRIA pricelist nova por linha. Re-importar duplica.
  Decisao consultiva: validar se queremos comportamento idempotente
  (search-then-create) ou se a duplicacao serve para historizar.
- O matching de template usa ``int(row['...'].split('_')[-1])``
  diretamente - se o external id mudar de formato (Odoo 18+
  alterou), parte.
- Sem rollback: erro a meio do Excel deixa pricelists
  parcialmente criadas. Considerar wrap em try/except + revert na
  proxima iteracao.
- Currency e fixa = moeda da company.
""",
    'author': 'Parametro Global',
    'depends': ['base', 'product'],
    'data': [
        'views/pricelists_import_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}
