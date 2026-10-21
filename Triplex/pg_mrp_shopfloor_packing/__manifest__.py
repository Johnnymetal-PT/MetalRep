# -*- coding: utf-8 -*-
{
    "name": "PG MRP Shop Floor Packing List",
    "summary": "Obriga o preenchimento do packing list do produto final ao fechar a produção no Shop Floor",
    "version": "17.0.1.0.0",
    "category": "Manufacturing",
    "description": """
PG MRP Shop Floor Packing List
==============================

Objetivo de negócio
-------------------
No Shop Floor (Chão de Fábrica), antes de o operador fechar a Ordem de Fabrico
("Fechar produção"), apresentar um popup que obriga a preencher/retificar o packing
list do produto final (volumes, peso e dimensões C/A/L por volume). Os valores já
existentes aparecem pré-preenchidos para retificação, e só após guardar é que a
produção fecha.

Pré-requisitos
--------------
- Módulos: `mrp_workorder` (app Shop Floor), `pg_packing_list_triplex` (define os
  campos `packing_*` no produto, ligados aos campos Studio `x_studio_*`).
- O produto final tem de existir; os valores são gravados no `product.template`
  (através do `product.product` da ordem), pelo que ficam reutilizáveis em futuras
  ordens/entregas do mesmo produto.

Como funciona
-------------
Patches OWL (sem modelos Python):
- `packing_dialog.js` + `packing_dialog.xml`: diálogo com os campos do packing list.
  As linhas de dimensões (Comprimento/Altura/Largura) são geradas conforme o número
  de volumes indicado; a Cubicagem é mostrada calculada em tempo real. Todos os campos
  visíveis são obrigatórios (volumes e peso > 0, e C/A/L > 0 para cada volume).
- `mrp_display_record_packing_patch.js`: intercepta o fecho da produção em ambas as
  vias do Shop Floor (`validate` no cartão da produção e `onClickCloseProduction` no
  botão verde do cartão da operação). Abre o diálogo, grava no produto e só depois
  deixa o fluxo standard concluir. Se o operador cancelar, a produção não fecha.

Passo a passo de utilização
---------------------------
1. No Shop Floor, concluir as operações e carregar em "Fechar produção".
2. Preencher/retificar o packing list do produto final no popup e guardar.
3. A produção fecha normalmente; os valores ficam no produto para o packing list/entrega.

Pontos de atenção
-----------------
- Depende da estrutura interna do `mrp_workorder` (componente MrpDisplayRecord); uma
  atualização major do Odoo pode exigir revisão dos patches.
- Os valores são gravados ao nível do produto (template), logo retificar afeta também
  futuras ordens/entregas do mesmo produto.
""",
    "depends": ["mrp_workorder", "pg_packing_list_triplex", "web"],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_packing/static/src/js/packing_dialog.js",
            "pg_mrp_shopfloor_packing/static/src/xml/packing_dialog.xml",
            "pg_mrp_shopfloor_packing/static/src/js/mrp_display_record_packing_patch.js",
        ]
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
