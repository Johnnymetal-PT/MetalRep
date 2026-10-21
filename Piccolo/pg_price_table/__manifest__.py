# -*- coding: utf-8 -*-
{
    'name': 'PG Dynamic Consumption Table for Manufacturing Orders',
    'version': '17.0.1.0.0',
    'summary': 'Tabela de consumo por quantidade no product.template (price_1..price_10) usada pelo pg_tecidos e por overrides de mrp.production para ajustar dinamicamente "Para Consumir" em funcao do product_qty.',
    'sequence': 1,
    'category': 'Manufacturing',
    'author': 'Parametro Global',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/product_template_views.xml',
    ],
    'description': """
PG Price Table (Tabela de Consumo)
==================================

a) Objetivo de negocio
----------------------
Componentes tipo "Tecido de Fornecedor" tem consumos por unidade
**nao linearmente proporcionais** a quantidade produzida (perdas de
corte, otimizacao de retalhos): para 1 cadeira gasta-se 1.20 m, para
2 gasta-se 2.10 m (nao 2.40 m), etc. Este modulo expoe uma tabela
``price_1..price_10`` no template do componente que e consultada
pela MO ao calcular "Para Consumir".

b) Pre-requisitos
-----------------
- Modulos standard ``mrp``, ``stock``.
- E pre-requisito de ``pg_tecidos`` (que tambem consome estes
  campos). Instalar primeiro este.

c) Como funciona
----------------
- ``models/product_template.py``:
  - Acrescenta 10 ``Float`` (``price_1..price_10``) em
    ``product.template``. Cada index representa a quantidade total
    em producao (1 a 10).

- ``models/mrp_production.py`` (override de ``create``):
  - Le ``product_qty`` da MO.
  - Calcula consumo do template principal via
    ``_get_consumption_value`` (mesma logica index = qty-1).
  - Sobrescreve ``vals['product_uom_qty']`` com o consumo (para
    a quantidade do **produto fabricado** corresponder ao consumo
    standard).
  - Especificamente para componente chamado "Tecido de Fornecedor":
    sobrescreve ``move.product_uom_qty`` no ``move_raw_ids`` com o
    consumo do **template principal** (nao do componente).

- ``views/product_template_views.xml``: tab "Tabela de Consumo" no
  formulario do produto com os 10 campos.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Backoffice > Produtos > abrir o template do componente.
3. Tab "Tabela de Consumo": preencher price_1..price_10 com o
   consumo total esperado para 1, 2, ..., 10 unidades produzidas.
4. Criar MO; "Para Consumir" reflete a linha N da tabela onde N =
   ``product_qty`` (capado a 10).

e) Exemplo pratico
------------------
Template "Cadeira X". Tabela:
- price_1=1.20, price_2=2.10, price_3=3.00, ... price_10=9.50.
MO para 3 cadeiras -> ``product_uom_qty = 3.00``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Consumo a zero"* -> tabela nao preenchida no template.
- *"Quantidade > 10 nao escala"* -> a tabela so tem 10 linhas; qty
  >= 10 usa ``price_10``. Em pratica Piccolo nao faz lotes > 10.
- *"Componente 'Tecido de Fornecedor' usa valores errados"* -> a
  logica especial em ``mrp_production.create`` usa o consumo do
  **template principal**, nao do componente. Para outros tecidos,
  a logica geral de ``pg_tecidos._apply_consumption_values`` aplica
  o consumo do componente.

g) Pontos de atencao / avisos
-----------------------------
- A tabela tem 10 slots fixos (price_1..price_10). Extender requer
  alteracao de modelo + view.
- O override de ``mrp.production.create`` neste modulo escreve em
  ``product_uom_qty`` do MO E em ``move.product_uom_qty`` quando o
  componente se chama exatamente "Tecido de Fornecedor".
- Existe sobreposicao com ``pg_tecidos`` (ambos overridam
  ``mrp.production.create``). Ordem de carregamento: a do MRO
  Python e definida pela ordem das ``depends``. Validar ordem para
  evitar uma sobrepor a outra de forma surpresa.
- Nomes ``price_*`` sao misleading - sao consumos, nao precos.
  Manter por compatibilidade com codigo existente.
""",
    'installable': True,
    'application': False,
    'auto_install': False,
}
