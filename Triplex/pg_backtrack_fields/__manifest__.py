{
    "name": "Backtrack SO and MO Fields to IN Picking",
    "version": "17.0.1.0.0",
    # `sale_stock` define `stock.picking.sale_id` (`sale_stock/models/stock.py`), usado para
    # resolver a venda nas devoluções, em que a origem aponta para outra guia e não para uma
    # compra. Sem esta dependência declarada, o campo podia não existir no arranque.
    "depends": ["stock", "mrp", "sale", "purchase", "sale_stock"],
    "author": "ChatGPT",
    "category": "Warehouse",
    "summary": "Traz para a receção (IN) a venda/ordem de fabrico de origem, para impressão de etiquetas",
    "description": """
Backtrack SO and MO Fields to IN Picking
========================================

Objetivo de negócio
-------------------
Numa receção de mercadoria (picking de entrada), poder saber de que encomenda de venda e
ordem de fabrico essa receção descende, para imprimir esses dados na etiqueta de receção.

Pré-requisitos
--------------
- Módulos: `stock`, `mrp`, `sale`, `purchase`.
- Os documentos têm de estar ligados pelo campo `origin` (comportamento standard do Odoo):
  picking.origin = PO.name, PO.origin = MO.name, MO.origin = SO.name.
- Campo Studio `x_studio_customer_ref` em `sale.order` (para a referência de cliente).
- Útil quando o circuito Compra -> Produção -> Receção é desencadeado a partir de uma venda
  com MTO/Make-to-Order.

Como funciona
-------------
Estende `stock.picking` com campos calculados (so_id, mo_id, so_name, customer_ref,
mo_product_id) que reconstroem a cadeia a partir do `origin`, apenas para pickings de
entrada (incoming):
  picking.origin -> purchase.order -> (PO.origin) -> mrp.production -> (MO.origin) -> sale.order
A referência do cliente vem de `so.x_studio_customer_ref` (campo Studio).

Passo a passo de utilização
---------------------------
1. Configurar produtos com MTO de modo que a venda gere a MO, e esta gere a PO.
2. Ao rececionar a mercadoria, abrir o picking de entrada e ver os novos campos:
   `Source SO`, `MO Product`, `Customer Reference`, etc.
3. Usar esses campos no template de etiqueta (ex.: `pg_print_zpl_label`).

Exemplo prático
---------------
Encomenda SO/0050 -> MO/0030 -> PO/0020 -> IN/0010. Ao abrir IN/0010, os campos calculados
exibem: SO/0050, x_studio_customer_ref="Cliente X", MO Product="Cadeira X". A etiqueta
ZPL impressa traz essa informação.

FAQ / Resolução de problemas
----------------------------
- P: Os campos vêm vazios.
  R: O picking não é de entrada (incoming) ou a cadeia origin->name não bate. Confirmar que
     os nomes dos documentos correspondem.
- P: Tenho `customer_ref` vazio mas a SO tem dados.
  R: O campo vem de `x_studio_customer_ref` (Studio); confirmar que existe e está preenchido.
- P: Funciona, mas falha quando dois documentos têm o mesmo nome.
  R: Limitação conhecida — search por nome devolve só um (limit=1).

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- A ligação entre documentos é feita por correspondência de NOME no campo `origin`.
  É frágil: depende de os nomes baterem certo e de não haver duplicados.
- Depende do campo Studio `x_studio_customer_ref` na venda.
- Estes campos (em especial `so_id`) são usados pelo módulo `pg_print_zpl_label`.
- Módulo gerado com apoio de IA (author "ChatGPT").
""",
    "data": [
        "views/stock_picking_views.xml"
    ],
    "installable": True,
    "application": False,
}
