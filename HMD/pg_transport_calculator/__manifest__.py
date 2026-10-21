# -*- coding: utf-8 -*-
{
    "name": "PG Transport Calculator",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://www.parametro.global",
    "category": "Sales",
    "summary": "Calculadora de transporte (cubicagem) com comparacao multi-transportadora e aplicacao automatica do custo na linha de venda.",
    "license": "LGPL-3",
    "description": """
PG Transport Calculator
=======================

Porta a calculadora de transportes da HMD (CUBICAGEM / calculadora online
hmdfurniture.github.io/Calculo) para dentro do Odoo, no orcamento.

a) Objetivo de negocio
----------------------
O comercial calculava o transporte fora do Odoo (Excel / web) e
transcrevia o valor. Este modulo permite calcular dentro do orcamento,
comparar varias transportadoras e aplicar o custo escolhido diretamente
na linha de venda do produto de transporte.

b) Modelos
----------
- ``pg.transport.carrier``: transportadora/tabela, com fatores de
  conversao volumetrica (``conv_m3``, ``conv_ldm``) e tipo
  (nacional/internacional). Motor de cubicagem em
  ``_compute_volumetric_weight`` (porta fiel de js/calculator.js).
- ``pg.transport.rate``: tarifa por pais/zona, com ``minimum`` e
  escaloes; ``_compute_cost`` calcula o custo para um peso.
- ``pg.transport.rate.tier``: escalao de peso (``weight_to`` superior,
  ``price``, ``flat``, ``scale_floor``, ``scale_cap``).

c) Calculo (fiel a calculadora online)
--------------------------------------
1. Por embalagem (caixa/palete, dims cm, qtd):
   - decisao LDM (so paletes, sem caixas, todas altas >125 e
     comprimento 100-125) vs m3;
   - ajustes de palete: comprimento 100-125 -> 120; altura >125 -> 250;
   - peso tarifario = volume * fator da transportadora.
2. Escalao por peso na tarifa do destino; custo:
   - escalao ``flat`` (nacional 1-50/51-100): custo = preco;
   - restantes: custo = ceil(peso/100) * preco, com limites
     ``scale_floor`` / ``scale_cap`` ao multiplicador;
   - custo >= ``minimum`` do destino.

d) Utilizacao
-------------
1. Vendas > Configuracao: definir o "Produto de Transporte".
2. Manutencao de tarifas: Vendas > Configuracao > Transporte
   (Transportadoras / Tarifas). Dados XBS Log (nacional + internacional)
   vem pre-carregados como seed (noupdate, nao sobrescritos em upgrade).
3. No orcamento, adicionar a linha do produto de transporte.
4. Botao "Calcular Transporte" -> introduzir pais/zona + embalagens ->
   "Calcular / Comparar" -> escolher transportadora -> "Aplicar".
   O ``price_unit`` da linha de transporte e atualizado.

e) Pontos de atencao
--------------------
- O seed XBS usa nomes de pais em PT e codigos de zona da tabela XBS.
- As tarifas sao mantidas pelo utilizador (Sales Manager) na UI.
- A calculadora de PRECOS de produto e tratada separadamente (Quote
  Calculator standard / hmd_sale_price_calculator).
""",
    "depends": ["sale_management", "sale_stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/xbslog_rates.xml",
        "views/transport_carrier_views.xml",
        "wizard/transport_calculator_wizard_views.xml",
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
}
