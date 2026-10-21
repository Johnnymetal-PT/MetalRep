# -*- coding: utf-8 -*-
#
# Manifesto do modulo PG Stock Route Hierarchy.
#
# Este modulo introduz uma hierarquia configuravel de armazens (primario,
# secundario, loja, fornecedor virtual) usada pelas vendas, pela
# disponibilidade no website e pelo calculo de stock teorico vindo do
# Hiper Sync. Depende de ``hiper_sync`` por causa do campo
# ``product.template.hiper_supplier_qty`` (stock externo importado).
#
# Idioma da documentacao: Portugues (Portugal).

{
    "name": "PG Stock Route Hierarchy",
    "summary": "Hierarquia de armazens (primario / secundario / loja / fornecedor virtual) para vendas, disponibilidade na loja online e stock teorico de fornecedor.",
    "description": """
PG Stock Route Hierarchy
========================

Adiciona a ``res.company`` quatro armazens hierarquicos que coordenam a forma
como o Odoo calcula stock vendavel, qty disponivel no website e routes de
reposicao para sales orders.

1. Objetivo de negocio
----------------------
O Hipermercado opera em multiplas localizacoes fisicas (almoxarife central,
distribuidor regional, loja fisica) e ainda integra catalogos de
fornecedores externos via ``hiper_sync``. Sem este modulo, o Odoo standard
permitiria reservar stock indistintamente em qualquer armazem da empresa, e a
disponibilidade na loja online nao consideraria a hierarquia de fulfillment.

O modulo resolve:

* uniformizar o armazem default das encomendas web (forca o "primario"),
* somar stock interno + stock virtual de fornecedor para o calculo de
  disponibilidade (``free_qty`` da linha de encomenda e da pagina de produto),
* configurar as rules ``mts_else_mto`` (make-to-stock else make-to-order) e
  os ``resupply_wh_ids`` automaticamente quando a hierarquia muda.

2. Pre-requisitos
-----------------
* Modulos: ``hiper_sync`` (para ``product.template.hiper_supplier_qty``),
  ``sale_stock``, ``purchase_stock``, ``website_sale_stock``.
* Pelo menos um armazem fisico criado em **Inventario > Armazens** por cada
  "nivel" da hierarquia que se queira utilizar (nao e obrigatorio preencher
  os quatro; o modulo so aplica os que estiverem definidos).
* O armazem ``Fornecedor Virtual`` deve ser usado apenas para fins de
  controlo (sem buy_to_resupply ativo). E ele que recebe a contribuicao
  vinda da sincronizacao do Hiper Sync.
* O utilizador que configura a hierarquia precisa de acesso a Definicoes
  (grupo ``base.group_system``) e a Inventario.

3. Como funciona
----------------
Modelos herdados (sem novos modelos):

* ``res.company`` -- acrescenta 4 ``Many2one`` para ``stock.warehouse`` mais
  um conjunto de helpers ``_pg_get_*`` que devolvem a hierarquia ordenada e
  somas de quantidade.
* ``res.config.settings`` -- expoe os 4 ``Many2one`` em **Definicoes >
  Inventario > PG Stock Hierarchy**.
* ``sale.order`` -- forca o ``warehouse_id`` ao primario nas encomendas com
  ``website_id`` e usa ``_pg_get_sale_available_qty`` em ``_get_free_qty``.
* ``sale.order.line`` -- em ``_read_qties`` substitui as quantidades por uma
  soma da hierarquia interna + supplier virtual, para a UI da venda mostrar
  o numero real "vendavel". Tambem injecta as routes de fornecimento
  configuradas em ``_prepare_procurement_values``.
* ``website`` -- ``_get_product_available_qty`` passa a usar a hierarquia,
  para a pagina publica do produto reflectir o mesmo total.

Quando se grava a configuracao (``write`` ou ``create``), ``res.company``
chama ``_pg_apply_stock_hierarchy()``, que:

1. Garante que nao ha armazens duplicados nem mistura de empresas
   (``_pg_validate_stock_hierarchy``).
2. Atualiza o ``ir.default`` de ``sale.order.warehouse_id`` para o primario.
3. Forca ``procure_method = 'mts_else_mto'`` nas delivery rules.
4. Atualiza ``resupply_wh_ids`` em cada armazem da hierarquia.
5. Desliga ``buy_to_resupply`` no armazem virtual de fornecedor (so e usado
   para visibilidade) e liga-o nos restantes.

4. Passo a passo de utilizacao
------------------------------
1. Aceder a **Inventario > Armazens** e criar (ou identificar) os armazens:
   primario, secundario, loja e fornecedor virtual.
2. Ir a **Definicoes > Inventario > PG Stock Hierarchy** e atribuir os 4
   campos. Gravar.
3. Confirmar que ``sale.order`` web passa a usar o primario como armazem
   default.
4. (Opcional) Sincronizar via ``hiper_sync`` para preencher
   ``hiper_supplier_qty`` nos produtos -- o calculo de qty website passa a
   incluir esse stock externo.
5. Acompanhar a disponibilidade na pagina de produto da loja online: o
   total mostrado e ``stock interno da hierarquia + supplier qty``.

5. Exemplo pratico
------------------
Empresa **"Hipermercado Portugal SA"**:

* Primario      = "Armazem Central" (1000 un. para varios SKUs);
* Secundario    = "Distribuidor Lisboa" (5000 un.);
* Loja          = "Loja Cascais" (200 un.);
* Fornecedor V. = "Fornecedores Externos" (qty derivada do Hiper Sync).

Encomenda web de 1x portatil:

1. A SO ``website_id`` -> ``warehouse_id`` = "Armazem Central" (forcado).
2. Linha calcula ``free_qty`` = central (10) + virtual (350 importados pelo
   Hiper Sync) = 360 unidades vendaveis.
3. Procurement gera reposicao via routes do "Armazem Central" se aplicavel,
   incluindo as rotas devolvidas por ``_pg_get_sale_supply_routes``.

6. FAQ e resolucao de problemas
-------------------------------
**P: "The configured PG warehouse hierarchy cannot contain duplicates."**
Causa: dois ou mais campos da hierarquia apontam para o mesmo armazem.
Resolucao: escolher armazens distintos. Se de facto sao iguais, deixar os
restantes em branco.

**P: "All warehouses in the PG hierarchy must belong to the same company."**
Causa: foi escolhido um armazem de outra ``res.company``.
Resolucao: criar armazens dedicados na empresa correta ou trocar a selecao.

**P: A encomenda do website nao usa o primario.**
Causa: a SO foi criada sem ``website_id`` (e.g. via backoffice / B2B) ou a
empresa nao tem ``pg_sale_primary_warehouse_id`` definido.
Resolucao: confirmar campos em Definicoes; para SOs internas, definir
manualmente o ``warehouse_id``.

**P: A loja online mostra "disponivel" mas a venda interna devolve 0.**
Causa: o stock vem todo de ``hiper_supplier_qty`` (fornecedor virtual) e
ainda nao houve compra para o armazem interno. O modulo soma os dois numeros
intencionalmente -- o produto vai ser fulfilled via compra ao fornecedor.
Resolucao: criar a route de compra (Make-to-Order) ou desativar a soma
custom alterando ``_pg_get_sale_available_qty``.

**P: As rules ficaram com ``procure_method`` diferente de ``mts_else_mto``.**
Causa: a hierarquia foi alterada e o ``_pg_apply_stock_hierarchy`` correu,
mas depois alguem mexeu manualmente nas rules.
Resolucao: gravar de novo a hierarquia em Definicoes -- volta a aplicar.

7. Pontos de atencao / avisos
-----------------------------
* O modulo nao cria stock.rule novas (transfers automaticos entre armazens
  da hierarquia). Se for desejado, configurar manualmente em
  **Inventario > Operacoes > Rules**.
* A logica multiempresa funciona, mas a configuracao e por empresa -- cada
  ``res.company`` tem o seu proprio conjunto de 4 armazens.
* ``hiper_supplier_qty`` so e somado se houver ``pg_sale_primary_warehouse_id``
  definido. Sem ele, o codigo cai para ``super()`` standard.
""",
    "version": "19.0.1.0.0",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "category": "Inventory/Inventory",
    "depends": [
        "hiper_sync",
        "sale_stock",
        "purchase_stock",
        "website_sale_stock",
    ],
    "data": [
        "views/pg_res_config_settings_views.xml",
    ],
    "installable": True,
}
