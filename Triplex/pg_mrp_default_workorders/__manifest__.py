# -*- coding: utf-8 -*-
{
    'name': 'pg MRP Centros de Trabalho por Defeito',
    'version': '17.0.1.0.0',
    'summary': 'Preenche por defeito as Ordens de Trabalho/Centros de Trabalho em todas as novas Ordens de Fabrico',
    'description': """
pg MRP Centros de Trabalho por Defeito
======================================

Objetivo de negócio
-------------------
Na Triplex o fluxo produtivo é uniforme (CORTE -> COSTURA -> ESPUMA -> ESTOFO ->
EMBALAGEM). O standard do Odoo só gera Ordens de Trabalho a partir das operações
da Lista de Materiais (BoM), pelo que não existe um "routing por defeito" aplicável
a todas as Ordens de Fabrico. Este módulo introduz uma lista configurável de centros
de trabalho por defeito e semeia automaticamente essas Ordens de Trabalho em todas as
novas Ordens de Fabrico que não tragam já operações da BoM.

Como funciona
-------------
- `pg.mrp.default.workorder`: lista configurável (por empresa) de centros de trabalho
  por defeito (sequência, nome da operação, centro de trabalho, duração prevista).
  Gerida em Fabrico -> Configuração -> Centros de Trabalho por Defeito.
- `mrp.production`:
    * ao criar uma Ordem de Fabrico que fique sem qualquer Ordem de Trabalho com centro
      de trabalho (tipicamente MOs sem BoM ou com BoM sem operações), semeia as Ordens de
      Trabalho a partir da configuração.
    * botão "Centros por defeito" no formulário e ação em lote na lista para atualizar
      Ordens de Fabrico existentes que não tenham qualquer centro de trabalho definido.

Notas (FACTOS OBSERVADOS no source 17.0)
----------------------------------------
- As Ordens de Trabalho semeadas são "manuais" (sem `operation_id`); o standard preserva-as
  nos recálculos de `_compute_workorder_ids` (só corre em draft e não apaga WOs sem operação).
- Quando a BoM já tem operações, o standard preenche-as e o módulo não duplica nada.
- A semeadura/atualização só ocorre em Ordens de Fabrico em estado `draft` ou `confirmed`.
""",
    'category': 'Manufacturing',
    'author': 'Parametro Global',
    'license': 'LGPL-3',

    'depends': ['mrp'],

    'data': [
        'security/ir.model.access.csv',
        'views/pg_mrp_default_workorder_views.xml',
        'views/mrp_production_views.xml',
    ],

    'installable': True,
    'application': False,
}
