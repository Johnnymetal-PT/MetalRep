{
    'name': 'pg_packing_list_confirm',
    'version': '1.0',
    'summary': 'Exige confirmação do packing list antes de validar a expedição',
    'description': """
pg_packing_list_confirm
=======================

Objetivo de negócio
-------------------
Garantir que nenhuma expedição (entrega) é validada sem que o packing list tenha sido
conferido e confirmado, evitando envios com dados de embalagem por rever.

Pré-requisitos
--------------
- Módulos: `stock`.
- Existir um campo packing list a confirmar (recomenda-se `pg_packing_list` ou
  `pg_packing_list_triplex` instalados em conjunto).
- A vista de stock.picking carregada (views/stock_picking_views.xml) — adiciona a checkbox.

Como funciona
-------------
Estende `stock.picking`:
- Campo `packing_list_confirmada` (booleano) que o utilizador marca quando o packing list
  está conferido.
- Override de `button_validate()`: se houver transferências de SAÍDA
  (`picking_type_code == 'outgoing'`) ainda não confirmadas, bloqueia com UserError. As
  restantes (entradas, internas) validam normalmente.

Passo a passo de utilização
---------------------------
1. Conferir todos os dados de embalagem na transferência de saída (dimensões, pesos, etc.).
2. Marcar a checkbox "Packing List Confirmada".
3. Validar a transferência. Se a checkbox estiver desmarcada, surge um erro a impedir.

Exemplo prático
---------------
Picking de saída SO/0001 com Packing List não confirmada -> ao "Validar", aparece um erro
em vermelho: "You must confirm the packing list before validating the delivery.". Após
marcar a checkbox e Validar de novo, a entrega segue normalmente.

FAQ / Resolução de problemas
----------------------------
- P: Não vejo a checkbox no formulário.
  R: A vista pode não estar carregada; verificar que `views/stock_picking_views.xml` está
     em `data` no manifesto e que o módulo foi atualizado.
- P: O bloqueio aparece em receções (entradas).
  R: Não deve — o módulo só bloqueia saídas (picking_type_code='outgoing'); se acontecer,
     reportar como bug.
- P: Quero exigir confirmação também para transferências internas.
  R: Editar o `filtered(...)` no override para incluir outros tipos.

Pontos de atenção
-----------------
- Aplica-se APENAS a transferências de SAÍDA.
- Complementa `pg_packing_list` (dados do packing list) e `pg_packing_list_triplex`.
- O controlo é a nível de UI/validação; não impede alterações via ORM/automação.
""",
    'category': 'Inventory',
    'depends': ['stock'],
    'data': [
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
