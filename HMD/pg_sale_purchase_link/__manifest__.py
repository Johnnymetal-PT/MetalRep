{
    "name": "PG Sale to Purchase Link",
    "version": "18.0.1.1.0",
    "category": "Sales",
    "summary": "Botoes smart na venda para abrir POs e MOs ligadas pelo procurement group.",
    "description": """
PG Sale to Purchase Link (HMD)
==============================

a) Objetivo de negocio
----------------------
Numa venda HMD com produtos make-to-order (MTO), o standard cria
automaticamente Purchase Orders (RFQ aos fornecedores) e Manufacturing
Orders (ordens de producao). Por defeito, ver tudo o que esta ligado a
essa venda exige navegar pelos procurements ou pelo origin. O modulo
adiciona dois botoes smart no formulario da venda - Purchase Orders e
Manufacturing Orders - que abrem listas filtradas. Tambem garante que
o renome da venda (ex.: passar de SO000123 para alguma forma final) se
propaga para os PO/MO ligados, mantendo o `origin` coerente.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `sale`, `purchase`, `sale_stock`, `mrp` (declarados em
  `depends`).
- A venda tem de gerar um `procurement.group` ao ser confirmada (e o
  comportamento standard quando ha produtos com rota MTO/Manufacture).

c) Como funciona (tecnico)
--------------------------
1. `sale.order` (`models/sale_order.py`):
   - `purchase_order_count` (Integer, computed): conta
     `purchase.order` cujo `group_id` == `procurement_group_id` da
     venda OU cujas linhas tem movimentos de destino nesse grupo
     (`order_line.move_dest_ids.group_id`): assim, depois de fundir
     RFQ (acao "Fundir"), a venda da RFQ cancelada ve a compra que
     ficou com as suas linhas. NAO usa `origin` para o count (mais
     robusto a renames).
   - `mrp_production_count` (Integer, computed): conta
     `mrp.production` cujo `procurement_group_id` == do SO.
   - `action_view_related_purchase_orders` /
     `action_view_related_mos`: act_window com `domain` no group_id e
     `create: False` no contexto (so para visualizacao).
   - Override de `action_confirm`: captura o nome antigo da venda
     antes do super (porque o standard pode renomear o SO de draft
     para sequencia confirmada) e, se mudou, faz `write` em todos os
     `purchase.order.origin` == old_name e `mrp.production.origin` ==
     old_name, sincronizando tambem `procurement_group_id` das MOs.

2. `mrp.production` (`models/mrp_production.py`):
   - Override de `create`: depois do super, chama
     `_update_procurement_group_from_sale()` que procura uma
     `sale.order` cujo nome bata certo com `production.origin` e
     atribui o `procurement_group_id` da venda a MO. Este hook
     completa o caso em que a MO e criada com `origin` mas sem
     `procurement_group_id` automatico.

3. View (`views/sale_order_views.xml`): adiciona ambos os botoes ao
   `button_box` standard.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_sale_purchase_link` na BD HMD.
2. Criar uma venda com produtos que disparem PO e/ou MO ao confirmar
   (rota make-to-order, route Manufacture configurada).
3. Confirmar a venda.
4. No topo do formulario da venda aparecem dois botoes smart:
     - "Purchase Orders" (carro de compras, conta as POs ligadas).
     - "Manufacturing Orders" (fabrica, conta as MOs ligadas).
5. Clicar em qualquer um abre a lista com `domain` filtrado pelo
   procurement group da venda.

e) Exemplo pratico
------------------
SO S00045 confirmada gera:
  - 2 RFQs ao mesmo fornecedor (linhas diferentes) -> PO P00021,
    P00022 com `group_id` == grupo do SO00045.
  - 1 MO MO/00007 com `procurement_group_id` == grupo do SO00045.

Botao "Purchase Orders" do SO00045 -> mostra P00021 e P00022.
Botao "Manufacturing Orders" do SO00045 -> mostra MO/00007.

Se o SO00045 for renomeado para "HMD-Cliente-X-2026" (manualmente ou
por outro modulo no `action_confirm`), o override sincroniza
`origin = 'HMD-Cliente-X-2026'` em P00021, P00022 e MO/00007 e em
qualquer outra MO ligada pelo nome antigo.

f) FAQ / Resolucao de problemas
-------------------------------
P: O botao "Purchase Orders" mostra 0 mas eu vejo POs com origin =
   nome do SO. Porque?
R: O count usa `group_id`, nao `origin`. Se a PO foi criada
   manualmente com origin = "S00045" sem fazer parte do procurement
   group, nao aparece no botao. Confirmar que a PO foi gerada pelo
   workflow MTO ou ligar manualmente ao mesmo `group_id`.

P: Confirmei a venda mas a MO criada nao tem `procurement_group_id`.
R: O override `_update_procurement_group_from_sale` corre no
   `create`. Se a MO foi criada antes do override (instalacao
   recente), correr um `flush` ou recriar a MO. Caso contrario,
   verificar que `production.origin` bate certo com `sale.name`
   (sensivel a renames).

P: Renomeei manualmente a venda e os PO/MO mantem o origin antigo.
R: O sync so corre dentro do `action_confirm`. Renames manuais
   posteriores nao disparam o write. Solucao: re-confirmar o SO
   (cancelar e confirmar de novo) ou atualizar manualmente.

P: O csv security `ir_attachment` esta neste modulo. Para que?
R: E uma ACL legada que abre `ir.attachment` ao `group_user` (RWUD =
   1,1,1,1). Em paralelo com `pg_attachment_universal_access`, e
   redundante mas inofensiva. Avaliar remocao na proxima limpeza.

g0) Cadeia da subcontratacao (v1.1.0, tarefa #8213)
---------------------------------------------------
O standard parte a cadeia venda -> compra ao subcontratado -> MO de
subcontratacao -> componentes: a MO nasce num grupo de aprovisionamento
novo e as compras de componentes so se chegam a partir da MO. Esta
versao deixa navegar nos dois sentidos, sem campos armazenados:
  - Venda: Subcontratacoes, Compras de componentes, Transferencias.
  - Compra: Vendas, Subcontratacoes, Consumida em (fabrico).
  - Fabrico: Vendas, Compra ao subcontratado.
Ver `models/subcontract_links.py`.

g) Pontos de atencao / avisos
-----------------------------
- O override `action_confirm` faz comparacao de nomes: se uma venda
  tiver mais que uma transicao de nome no mesmo confirm, perde-se a
  ligacao intermedia. Cenario raro mas a vigiar.
- O `mrp.production.create` override faz uma `search` por nome -
  custo linear ao numero de SOs. Aceitavel em volume HMD.
- O ACL `access_ir_attachment_user` neste modulo expoe ir.attachment
  para `base.group_user` (RWUD). Verificar interaccao com
  `pg_attachment_universal_access` antes de instalar ambos.
- O nome dos campos esta em ingles (`purchase_order_count`,
  `mrp_production_count`) - manter convencao do standard.
""",
    "author": "Parametro Global",
    "website": "https://parametro.global",
    "license": "LGPL-3",
    "depends": [
        "sale", "purchase", "sale_stock", "mrp",
        "sale_purchase", "purchase_mrp", "mrp_subcontracting",
        "mrp_subcontracting_purchase",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
        "views/subcontract_links_views.xml",
    ],
    "installable": True,
}
