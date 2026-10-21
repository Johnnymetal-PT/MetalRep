# -*- coding: utf-8 -*-
#
# Manifesto do modulo Hiper Sync Core.
#
# Este modulo e o nucleo de sincronizacao de feeds de fornecedores do Hipermercado:
# importa catalogos externos (FTP/CSV/JSON/Crawler), normaliza-os, traduz texto,
# aplica regras de margem por categoria e publica os produtos resultantes no
# catalogo interno e na loja online. Os outros modulos custom (em particular
# pg_stock_route_hierarchy) dependem deste para o conceito de fornecedor virtual.
#
# Idioma da documentacao: Portugues (Portugal). Codigo e UI em ingles tecnico.

{
    "name": "Hiper Sync Core",
    "summary": "Sincronizacao de feeds de fornecedores (FTP/CSV/JSON/crawler) e publicacao no catalogo Odoo + loja online do Hipermercado.",
    "description": """
Hiper Sync Core
===============

Modulo central de integracao de fornecedores do Hipermercado. Importa catalogos
externos, normaliza dados, traduz texto, aplica regras de margem por categoria
e publica produtos no Odoo e na loja online.

1. Objetivo de negocio
----------------------
Substituir a manutencao manual de catalogo (alta de produtos, atualizacao de
precos e stock por fornecedor) por um fluxo automatizado, multifornecedor e
auditavel. Resolve:

* duplicacao de produtos entre fornecedores (merge por EAN/referencia/fingerprint),
* tempo gasto a copiar precos e stock dos catalogos externos,
* publicacao manual de produtos sem stock ou sem preco na loja,
* falta de rasto de execucao quando uma sincronizacao falha.

2. Pre-requisitos
-----------------
Pre-requisitos tecnicos:

* Odoo 19.0 Enterprise.
* Modulos dependentes instalados: ``stock``, ``website_sale_stock``, ``mail``,
  ``emipro_theme_base``.
* Biblioteca Python ``requests`` disponivel no ambiente Odoo.
* Acesso de rede a saida (FTP/HTTPS) para os fornecedores configurados.

Pre-requisitos funcionais antes do primeiro sync:

* Configurar pelo menos um armazem em **Inventario > Armazens** (sugestao:
  criar um armazem "Fornecedor Virtual" usado pelo modulo
  ``pg_stock_route_hierarchy`` para representar stock externo).
* Definir um parceiro fornecedor (``res.partner`` com ``supplier_rank > 0``)
  por cada fornecedor real, ou deixar que o modulo crie automaticamente.
* Categorias internas e categorias publicas (website) para o mapeamento; um
  fallback (Default Internal Category / Default Website Category) e
  obrigatorio para fornecedores que nao tenham todos os mapeamentos cobertos.
* Se ``translate_enabled`` for ativado: chave API valida em
  **Definicoes > Hiper Sync** para o provedor escolhido (OpenAI ou Google).
* Se for usado o modo *Remote Crawler*: configurar o webhook do crawler externo
  (``remote_crawler_trigger_url`` e ``remote_crawler_status_url``) e o token
  ``hiper_sync.remote_crawler_upload_token`` em **Parametros do sistema**.

3. Como funciona
----------------
Modelos novos criados pelo modulo:

* ``hiper.sync.vendor`` -- ficha de fornecedor (credenciais, mapeamento de
  categorias, regras de margem, parametros de traducao, configuracao do crawler
  remoto). E o ponto de entrada operacional.
* ``hiper.sync.run`` -- execucao de uma sincronizacao (fila + estado +
  progresso). Suporta ``queued``, ``running``, ``paused``, ``done``,
  ``done_warning``, ``failed`` e ``cancelled``.
* ``hiper.sync.run.line`` -- detalhe linha-a-linha do que foi importado /
  publicado / saltado / falhado.
* ``hiper.sync.category.map`` -- mapeamento categoria_fornecedor ->
  categoria_interna / categoria_publica, com ``shipping_cost``,
  ``margin_percent``, ``extra_margin_percent`` e ``origin_discount_percent``.
* ``hiper.product.feature.line`` -- features importadas (chave/valor) por
  produto.
* ``pg.product.image`` -- imagens auxiliares importadas.

Modelos herdados:

* ``product.template`` -- estado de sincronizacao, locks granulares (nome,
  descricoes, preco, categorias, imagens, features), fila assincrona de
  imagens (campo ``hiper_image_sync_state``).
* ``res.config.settings`` -- chaves de traducao, defaults de modelo IA, etc.

Servicos (em ``services/``):

* ``vendor_adapters`` -- factory que devolve o adapter certo para cada
  ``source_kind`` (``ftp_csv``, ``csv_url``, ``json_url``, ``crawler_csv``,
  ``local_csv``).
* ``adapter_base`` -- normaliza CSV/JSON em registos comuns
  (``reference``, ``ean13``, ``name``, ``unit_price``, ``quantity``,
  ``category``, ``sub_category``, ``brand``, ``description``, ...).
* ``merger`` -- decide se uma linha do feed e novo produto, atualizacao por
  barcode, referencia ou fingerprint.
* ``publisher`` -- aplica regras de publicacao: stock minimo, preco minimo,
  ``hiper_lock_*``, multi-fornecedor.
* ``translate`` -- traducao via OpenAI ou Google Translate, com termos
  protegidos (marca, referencia, EAN13).
* ``pg_term_discovery`` -- auto-descoberta de termos protegidos via
  Wikipedia/Wikidata e (opcional) GTIN.
* ``utils`` -- helpers de parsing JSON e limpeza de HTML.

Controllers:

* ``pg_remote_crawler`` -- endpoint ``/hiper_sync/crawler/upload`` que aceita
  um CSV gerado por crawler externo (autenticacao Bearer com o token em
  ``ir.config_parameter`` ``hiper_sync.remote_crawler_upload_token``).

Crons (definidos em ``data/ir_cron.xml``):

* ``ir_cron_hiper_sync_queue`` (1 min) -- worker que processa a fila de runs.
* ``ir_cron_hiper_sync_full`` (4 h, desativado por defeito) -- full sync a
  todos os fornecedores ativos.
* ``ir_cron_hiper_pending_images`` (1 min) -- descarrega assincronamente as
  imagens pendentes (``hiper_image_sync_state = queued``).
* ``ir_cron_pg_remote_crawler_prewarm`` (10 min) -- dispara os crawlers
  remotos a horas configuradas (``pg_remote_crawler_trigger_time``).

4. Passo a passo de utilizacao
------------------------------
**Onboarding de um novo fornecedor**

1. Aceder a **Hiper Sync > Fornecedores** e criar um registo.
2. Preencher ``Name`` (comercial) e ``Code`` (identificador tecnico unico).
3. Escolher ``Source Kind`` consoante a fonte: FTP, URL CSV, JSON, crawler ou
   ficheiro local.
4. Preencher as credenciais correspondentes (FTP host/user/password,
   ``feed_url``, ``api_url_template``, etc.).
5. Se necessario, escolher ``pg_adapter_mode = Generic Mapping`` e preencher
   ``pg_mapping_json`` para feeds simples; caso contrario manter
   ``Code Adapter`` (adapter Python registado pelo codigo do fornecedor).
6. Definir ``default_categ_id`` (categoria interna fallback) e
   ``default_public_categ_id`` (categoria website fallback).
7. Adicionar pelo menos um registo em ``category_map_ids`` por categoria do
   fornecedor que se queira mapear, com regras de margem.
8. (Opcional) Ativar ``translate_enabled``, escolher provider e preencher a
   chave API (vendor-specific ou global em Definicoes).
9. Clicar **Validate Configuration** para garantir que nao faltam campos.
10. Clicar **Preview Feed** para uma extracao sem publicar: confirma headers,
    contagem de linhas, EAN invalidos, etc.

**Executar uma sincronizacao**

1. No formulario do fornecedor, clicar **Run Sync** (so esse fornecedor) ou
   **Run Full Sync** (todos os fornecedores ativos).
2. Acompanhar a execucao em **Hiper Sync > Sync Runs**: progresso em
   percentagem, fornecedor corrente, registos processados / esperados, ETA.
3. Se necessario, **Pause** (espera ponto seguro) ou **Cancel** (cancela apos
   o item atual). **Force Cancel** termina imediatamente.

**Modo Remote Crawler**

1. Definir ``source_kind = csv_url`` e ``remote_crawler_trigger_url`` +
   ``remote_crawler_status_url``.
2. Definir ``pg_remote_crawler_trigger_time`` (HH:MM em UTC) para o crawler
   ser disparado automaticamente todos os dias pelo cron de prewarm.
3. Regerar o token via **Regenerate Crawler Token** e configura-lo no
   crawler externo (Bearer).
4. Quando o crawler termina, faz POST de upload para
   ``/hiper_sync/crawler/upload`` -- o feed fica disponivel para o proximo
   sync.

5. Exemplo pratico
------------------
Fornecedor **Eldisser B2B** com feed gerado por crawler remoto:

* ``name`` = "Eldisser"; ``code`` = "eldisser"; ``source_kind`` = ``csv_url``.
* ``remote_crawler_trigger_url`` = "https://crawler.example.com/crawl/start".
* ``remote_crawler_status_url`` = "https://crawler.example.com/jobs/{job_id}".
* ``pg_remote_crawler_trigger_time`` = "01:30" (UTC).
* ``pg_remote_crawler_max_age_minutes`` = 360 (CSV valido durante 6 h).
* ``pg_remote_crawler_force_tienda_view`` = True (forca vista loja no
  scraping).

Mapeamento de categorias:

* "Informatica > Portateis" --> ``Informatica/Portateis`` (interna) +
  ``INFORMATICA > Portateis`` (publica),
  ``shipping_cost`` = 3.50, ``margin_percent`` = 15, ``extra_margin_percent`` = 5.

Fluxo diario esperado:

1. 01:30 UTC, ``cron_prepare_remote_crawlers`` dispara o crawler externo.
2. O crawler scrapes o site B2B, gera o CSV e publica-o em
   ``/hiper_sync/crawler/upload`` com Bearer token.
3. O primeiro **Run Full Sync** do dia (manual ou cron) deteta o feed pronto,
   normaliza, traduz, aplica margens, faz merge com o catalogo e publica.
4. Produtos com ``hiper_supplier_qty = 0`` ficam despublicados se
   ``ignore_out_of_stock_products`` estiver ativado.

6. FAQ e resolucao de problemas
-------------------------------
**P: "Remote crawler job triggered. Wait for completion, then refresh."**
Causa: o sync foi pedido antes do crawler externo ter um CSV pronto.
Resolucao: aguardar (5-10 min em media) ou clicar **Refresh Remote Crawler**.

**P: "Translation skipped: OpenAI API key is not configured"**
Causa: ``translate_enabled = True`` mas falta a chave da OpenAI.
Resolucao: preencher em **Definicoes > Hiper Sync** (global) ou em
``translate_api_key`` no proprio fornecedor.

**P: O sync esta marcado como ``failed`` por timeout de worker.**
Causa: o cron worker bloqueou e nao houve heartbeat dentro de
``_stale_timeout_minutes`` (30 min, 18 min em publish).
Resolucao: o proprio ``cron_process_queued_runs`` chama ``_recover_stale_runs``
e re-enfileira o run (ate ``_stale_retry_limit = 3`` vezes). Apos 3 retries,
investigar logs.

**P: Linhas com ``invalid/missing EAN`` no diagnostico.**
Causa: o feed do fornecedor traz EANs vazios ou com checksum invalido. O
adapter descarta essas linhas, sao reportadas em
``diagnostics["invalid_ean_count"]``.
Resolucao: pedir ao fornecedor para corrigir o feed, ou ajustar o
``pg_mapping_json`` para usar outro identificador (referencia).

**P: O preco final nao reflete a margem esperada.**
Causa: nao existe mapeamento explicito ``hiper.sync.category.map`` para a
categoria do feed; foi usado o fallback ``default_categ_id`` sem margem.
Resolucao: adicionar mapeamento explicito ou definir margens no fallback.

**P: O cron de queue parece nao processar runs.**
Causa: o registo do cron ``hiper_sync.ir_cron_hiper_sync_queue`` esta
desativado ou em execucao prolongada.
Resolucao: confirmar em **Definicoes Tecnicas > Acoes Automatizadas** que
``Active = True`` e ``nextcall`` esta no futuro proximo.

7. Pontos de atencao / avisos
-----------------------------
* O modulo executa ``self.env.cr.commit()`` em pontos criticos (apos atualizar
  estado de cron, apos cada checkpoint de progresso). E intencional para nao
  perder estado em caso de timeout do worker; nao remover.
* ``pg_translate_discovery_preset`` contem uma lista hardcoded de categorias do
  Hipermercado (INFORMATICA, ELETRODOMESTICOS, IMAGEM E SOM, ESPACO CRIANCA,
  GEEK ZONE, MOBILIDADE, OUTLET HOT, OFERTAS FLASH HOT). Acompanhar a evolucao
  da arvore de categorias publicas se forem renomeadas.
* O modulo confia em ``hiper.sync.vendor.code`` como identificador estavel.
  Renomear ``code`` invalida todos os ``product.template.hiper_source_module_code``
  ja sincronizados.
* O endpoint ``/hiper_sync/crawler/upload`` aceita ficheiros grandes -- proteger
  por firewall ou rate-limit do reverse proxy se exposto a internet.
""",
    "version": "19.0.6.0.0",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "category": "Inventory/Inventory",
    "depends": [
        "stock",
        "website_sale_stock",
        "mail",
        "emipro_theme_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/vendor_data.xml",
        "data/ir_cron.xml",
        "views/menu_views.xml",
        "views/vendor_views.xml",
        "views/sync_run_views.xml",
        "views/product_template_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hiper_sync/static/src/js/sync_run_auto_refresh.js",
        ],
    },
    "installable": True,
    "application": True,
}
