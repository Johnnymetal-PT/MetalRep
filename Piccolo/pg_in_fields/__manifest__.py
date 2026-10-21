# -*- coding: utf-8 -*-
{
    'name': 'PG Stock Picking SO Reference',
    'version': '17.0.1.0.0',
    'summary': 'Propaga Cliente, Referencia do Cliente e nome da Encomenda da Sale Order original ate ao Stock Picking de entrada de componentes.',
    'author': 'Parametro Global',
    'depends': ['stock', 'purchase', 'sale', 'mrp'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'description': """
PG In Fields
============

a) Objetivo de negocio
----------------------
No fluxo MTO da Piccolo, quando chega ao armazem um Stock Picking de
entrada (compra de componentes), o operador precisa de saber a que
Sale Order/cliente final esse material esta destinado. Standard Odoo
so mostra a PO ou MO no campo ``origin`` - aqui resolve-se a cadeia
ate ao SO.

b) Pre-requisitos
-----------------
- Modulos standard ``stock``, ``purchase``, ``sale``, ``mrp``.
- Fluxo "SO -> MO -> PO -> Picking" onde o campo ``origin`` esta
  preenchido em cada salto (e o comportamento standard MTO).
- Os campos sao **prefixados ``x_studio_``** - foram criados
  originalmente em Studio e mantidos para compatibilidade com vistas
  Studio existentes.

c) Como funciona
----------------
- Override de ``stock.picking`` em ``models/stock_picking.py``.
- Tres campos computados, dependentes de ``origin``:
  - ``x_studio_cliente_1`` (Many2one res.partner)
  - ``x_studio_referncia_do_cliente_2`` (Char) (sic - typo herdado de
    Studio, **nao renomear** sem migration porque ha vistas Studio a
    referenciar este nome literal)
  - ``x_studio_sale_order_name`` (Char)
- Algoritmo (``_compute_so_fields``):
  1. Cada picking arranca com os 3 campos a False.
  2. Se ``origin`` esta preenchido, procura ``purchase.order`` com
     ``name == origin``.
  3. Da PO obtem ``origin`` da PO (= nome da MO) e procura
     ``mrp.production``.
  4. Da MO obtem ``origin`` da MO (= nome da SO) e procura
     ``sale.order``.
  5. Atribui ``partner_id``, ``client_order_ref`` e ``name`` da SO.
- ``store=True`` garante que os valores ficam pesquisaveis em
  listas/filtros.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Confirmar fluxo standard: SO -> MO criada -> PO de componentes
   gerada -> Receipt picking dessa PO.
3. Abrir o picking: ja aparece o cliente, ref do cliente e nome da SO.

e) Exemplo pratico
------------------
``SO S00123`` para cliente "Hotel XYZ" gera ``MO/00045`` que origina
``PO P00210`` (componentes). Ao receber ``WH/IN/00301`` desse PO,
o picking mostra ``Cliente = Hotel XYZ``, ``Ref Cliente = OC-2026-87``,
``Encomenda = S00123``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Campos vazios mesmo com origin"* -> a cadeia partiu-se algures
  (ex.: nome da PO nao coincide com o que esta em ``origin`` do
  picking). Verificar manualmente: 1) PO existe?, 2) PO.origin = MO
  ainda existe?, 3) MO.origin = SO ainda existe?.
- *"Typo em x_studio_referncia_do_cliente_2"* -> proposital, nao
  renomear sem fazer migration manual nas views Studio. Adicionar uma
  label correta em vez disso.

g) Pontos de atencao / avisos
-----------------------------
- A cadeia PO -> MO -> SO depende do ``origin`` ser preservado tal e
  qual (string match). Qualquer custom que reformate o ``origin``
  rebenta esta logica.
- Faz 3 ``search()`` por picking computado - aceitavel para a
  cardinalidade tipica; nao recalcular em massa para milhares de
  pickings sem store=True ja em base.
""",
    'installable': True,
    'application': False,
}
