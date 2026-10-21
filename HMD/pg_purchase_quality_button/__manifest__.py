# -*- coding: utf-8 -*-
{
    'name': 'PG Purchase Quality Button',
    'version': '18.0.1.0.0',
    'summary': 'Botao smart "Qualidade" na encomenda de compra - lista as verificacoes de qualidade das rececoes.',
    'description': """
PG Purchase Quality Button
==========================

a) Objetivo de negocio
----------------------
Na HMD, a qualidade dos artigos e verificada na rececao das compras
(quality.check ligadas aos pickings de entrada). O standard nao da, na
propria encomenda de compra, um atalho para ver as verificacoes de
qualidade associadas. Este modulo adiciona um botao smart "Qualidade"
no formulario da `purchase.order` que conta e abre as `quality.check`
das rececoes dessa encomenda.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `purchase_stock` (da o campo `purchase.order.picking_ids`) e
  `quality_control` (integra `quality.check` com os pickings de stock).
- As verificacoes de qualidade tem de estar ligadas aos pickings
  (campo `quality.check.picking_id`), o que e o comportamento standard
  quando ha pontos de controlo sobre o tipo de operacao de rececao.

c) Como funciona (tecnico)
--------------------------
1. `purchase.order.quality_check_count` (campo Integer calculado,
   `compute_sudo=True`): conta as `quality.check` cujo `picking_id`
   pertence aos `picking_ids` da encomenda. `compute_sudo` garante que
   a contagem aparece mesmo a utilizadores sem leitura direta de QC.
2. `purchase.order.action_view_quality_checks`: devolve uma
   `ir.actions.act_window` sobre `quality.check` com dominio
   `picking_id in picking_ids` da encomenda. Construida em codigo (sem
   depender de um xmlid de acao) para ser robusta entre versoes.
3. View (`views/purchase_order_views.xml`): botao smart no
   `oe_button_box` do form da encomenda, restrito ao grupo
   `quality.group_quality_user` (mesmo criterio dos botoes QC
   standard), evitando erros de acesso ao clicar.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_purchase_quality_button`.
2. Compras > Encomendas > abrir uma encomenda com rececoes.
3. No topo aparece o botao smart "Qualidade" com a contagem.
4. Clicar abre a lista das verificacoes de qualidade dessas rececoes
   (o estado Aprovado/Reprovado fica visivel na coluna de estado).

e) Pontos de atencao / avisos
-----------------------------
- A contagem inclui TODAS as verificacoes das rececoes (aprovadas e
  reprovadas). Para ver so as reprovadas, filtrar por Estado na lista.
- O botao so e visivel a utilizadores do grupo
  `quality.group_quality_user` (igual ao standard).
- Sem desenvolvimento sobre `vendor/odoo_src`; apenas heranca de
  modelo e de vista no namespace `pg_`.
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['purchase_stock', 'quality_control'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
}
