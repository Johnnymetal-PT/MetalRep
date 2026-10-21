# -*- coding: utf-8 -*-
{
    'name': 'PG Variant Update',
    'version': '17.0.1.0.0',
    'summary': 'Wizard que atualiza campos Volume / Quantidade Volume nas variantes a partir de um Excel (matching por Nome + Valor de Variante).',
    'author': 'Parametro Global',
    'category': 'Product',
    'depends': ['product'],
    'data': [
        'views/product_template_views.xml',
        'views/product_variant_update_wizard_views.xml',
        'data/ir.model.access.csv',
    ],
    'description': """
PG Variant Update
=================

a) Objetivo de negocio
----------------------
Atualizar em batch os campos logisticos ``volume`` e
``quantidade_volume`` (criados em Studio) das variantes do catalogo
a partir de um Excel. Util quando o departamento de expedicao
recalcula cubicagens fora do Odoo.

b) Pre-requisitos
-----------------
- Modulo standard ``product``.
- Bibliotecas Python: ``pandas`` + ``openpyxl``.
- Campos ``volume`` e ``quantidade_volume`` em ``product.product``
  (Studio ou Odoo standard - validar).
- Excel com colunas:
  - ``Nome`` -> nome do produto (= ``product.product.name``).
  - ``Valores de Variante`` -> nome do valor de atributo da variante
    (singular: o wizard espera uma so variante por match).
  - ``Volume`` -> valor a escrever.
  - ``Quantidade Volume`` -> valor a escrever.

c) Como funciona
----------------
- ``models/product_variant_update.py``:
  - ``product.variant.update.wizard`` recebe Excel.
  - Para cada linha:
    1. ``product.product.search([('name', '=', row['Nome']),
       ('attribute_value_ids.name', '=', row['Valores de Variante'])])``.
    2. Se encontrar, ``write({'volume': ..., 'quantidade_volume': ...})``.
  - Devolve reload para o utilizador ver os resultados na vista.

d) Passo a passo de utilizacao
------------------------------
1. Instalar (garantir pandas + openpyxl).
2. Inventario > abrir um produto -> botao "Update Variants" (vista
   do template).
3. Upload do Excel.
4. As variantes que combinam (nome + valor) recebem os valores.

e) Exemplo pratico
------------------
Excel:
- Nome="Cadeira X", Valores de Variante="Linho Bege", Volume=0.18,
  Quantidade Volume=1
- Nome="Cadeira X", Valores de Variante="Linho Castanho", Volume=0.18,
  Quantidade Volume=1

Resultado: as duas variantes "Linho Bege" e "Linho Castanho" do
"Cadeira X" ficam com volume=0.18 e quantidade_volume=1.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Variante nao atualiza"* -> nome do produto ou valor de variante
  com case diferente / espacos. O search e case-sensitive.
- *"Atributo errado a atualizar"* -> o match e por
  ``attribute_value_ids.name`` (qualquer atributo). Se houver dois
  atributos com o mesmo nome de valor (ex.: "Bege" em "TECIDO" e
  "COR"), o ``limit=1`` apanha o primeiro -> incorreto. Validar
  catalogo.

g) Pontos de atencao / avisos
-----------------------------
- O wizard nao distingue qual o atributo do valor pesquisado -
  ``attribute_value_ids.name`` corre transversalmente. Para evitar
  colisoes, garantir nomes unicos entre atributos.
- Sem feedback de quantas variantes foram atualizadas - apenas
  faz reload. Para auditoria, considerar acrescentar log/aviso na
  resposta.
- Os campos ``volume`` e ``quantidade_volume`` podem ser standard
  (``product.template.volume``) ou Studio. **Validar na BD antes
  de assumir.**
""",
    'installable': True,
    'application': False,
}
