# -*- coding: utf-8 -*-
{
    "name": "PG BD Connection",
    "version": "17.0.1.0.0",
    "summary": "Replica faturas, pagamentos e guias da BD principal (Odoo Enterprise PICCOLO) para a BD Community (PICCOLO_COMMUNITY) chamando o registry diretamente, sem XML-RPC.",
    "author": "Parametro Global",
    "category": "Accounting",
    "depends": ["account", "sale", "account_reports", "stock", "web"],
    "data": [
        "views/account_move_view.xml",
        "views/stock_picking_view.xml",
        "views/report_ledger_highlight.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_bd_connection/static/src/scss/account_report.scss",
        ],
        "account_reports.assets_pdf_export": [
            "pg_bd_connection/static/src/css/account_report_pdf.css",
        ],
    },
    "description": """
PG BD Connection
================

a) Objetivo de negocio
----------------------
A Piccolo opera duas BDs Odoo no mesmo servidor: a principal **PICCOLO**
(Enterprise, fluxo comercial/producao) e a secundaria
**PICCOLO_COMMUNITY** (Community, foco contabilistico). Este modulo
sincroniza faturas, pagamentos e guias entre as duas BDs **sem**
sair do processo Odoo (usa ``odoo.registry()`` em vez de XML-RPC),
clicando num botao na BD principal.

b) Pre-requisitos
-----------------
- As duas BDs (**PICCOLO** e **PICCOLO_COMMUNITY**) tem de estar no
  mesmo processo/servidor Odoo (mesmo registry).
- Utilizador autenticado existe em ambas as BDs (matching por
  ``self.env.uid``).
- BD destino tem de ter:
  - Diario de venda (``account.journal`` com ``type=sale`` e
    ``default_account_id`` preenchido).
  - Diario "fixo" para pagamentos: ``journal_id = 14`` (HARDCODED -
    ver "Pontos de atencao").
  - Pelo menos uma ``account.payment.method.line``.
- BD principal tem o campo ``x_studio_community`` (boolean) em
  ``account.move`` (Studio) - usado como flag de "ja sincronizado".
- ``pg_bd_connection_fields`` instalado na **BD secundaria** para
  garantir os campos ``x_studio_volumes_3``, ``x_studio_peso_kg_1``,
  ``x_studio_cubicagem_1`` em ``stock.move``, ``x_studio_zona`` em
  ``stock.picking`` e ``x_studio_observaes_no_recibo`` em
  ``account.payment``.

c) Como funciona
----------------
- ``models/account_move.py`` (``action_sync_invoice``):
  1. **Na BD principal**: muda ``journal_id`` para ``50`` (journal
     especifico Piccolo) e, se a fatura nao esta posted, posta-a.
  2. Abre cursor para a BD ``PICCOLO_COMMUNITY``; recupera todas
     ``res.company.ids`` e injeta-as em ``allowed_company_ids``.
  3. Garante coluna SQL ``account_move.delivery_count`` (via
     ``_ensure_column`` helper que executa ``ALTER TABLE`` se a
     coluna nao existir).
  4. Procura/cria ``res.partner`` por ``name`` (matching simples).
  5. Procura primeiro ``account.journal`` de venda; usa
     ``default_account_id`` como ``account_id`` das linhas.
  6. Re-cria as linhas (``invoice_line_ids``) ordenadas por
     ``sequence``, com matching de taxes por ``name``.
  7. Cria ``account.move`` no destino em estado ``draft``.
  8. Marca a fatura origem com ``x_studio_community=True``.

- ``models/account_payment.py`` (``action_sync_payment``):
  - Parsing do ``ref`` em multiplas faturas via
    ``_split_invoice_refs`` (split por ``,;\\n``).
  - Procura as faturas correspondentes na BD destino e cria UM
    pagamento agregado via ``account.payment.register``.
  - Journal HARDCODED ``14`` na destino.
  - Garante campo ``x_studio_observaes_no_recibo`` (cria como
    ``ir.model.fields`` manual se nao existir).
  - ``mark_as_sent``: utilitario para forcar reconciliacao de
    pagamentos manuais posted na BD principal (loop pelos refs).

- ``models/stock_picking.py`` (``action_sync_delivery``):
  - Helpers ``_find_or_create_product``, ``_find_picking_type``,
    ``_find_location``, ``_find_or_create_zona``.
  - Cria guia replicada com todos os moves (incluindo campos Studio
    ``x_studio_*`` se existirem no destino).
  - Confirma a guia no destino quando esta em ``draft/waiting/confirmed``.
  - Marca a origem com ``x_studio_community_delivery=True``.

- ``models/sale_order.py``: campo computed ``order_line_description``
  (concatena nomes das linhas) com search method - usado para
  filtros/relatorios.

- ``models/account_reports.py`` (estende Aged Receivable e Partner
  Ledger): limpa o ``name`` para mostrar so a primeira linha
  (``split("\\n")[0]``) e adiciona classe CSS ``partner-header`` para
  alinhamento no PDF.

- Assets CSS/SCSS: estilo de cabecalho de partner no relatorio.

d) Passo a passo de utilizacao
------------------------------
1. Garantir que **pg_bd_connection_fields** esta instalado na BD
   **PICCOLO_COMMUNITY**.
2. Instalar **pg_bd_connection** na BD **PICCOLO**.
3. Abrir uma fatura na BD principal -> botao "Sync to Community" no
   header.
4. Botao confirma a fatura (se draft), garante coluna sql necessaria
   no destino e cria a fatura replicada.
5. Para pagamentos: idem; o ``ref`` do pagamento tem de conter os
   nomes das faturas a reconciliar separados por ``,``, ``;`` ou
   nova linha.
6. Para guias: botao "Sync Delivery to Community".

e) Exemplo pratico
------------------
``INV/2026/0058`` em PICCOLO, draft, com 3 linhas e 2 taxas. Botao
"Sync to Community":
- Fatura passa a journal 50 em PICCOLO, posted.
- Em PICCOLO_COMMUNITY: cliente "Hotel XYZ" criado se nao existia,
  novo ``account.move`` em draft (move_type=out_invoice), linhas
  replicadas, ``x_original_invoice_id=58`` se o campo existir.
- INV/2026/0058 fica com ``x_studio_community=True``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Registry for database PICCOLO_COMMUNITY not found"* -> a BD nao
  esta no mesmo processo. Verificar ``--db-filter`` e que ambas as
  BDs estao registadas no mesmo workers pool.
- *"No sales journal found in second database"* -> falta criar um
  ``account.journal`` com ``type=sale`` na BD destino.
- *"Failed to create invoice ... taxes"* -> o matching de taxes e
  por ``name``. Se as taxes nao existem na BD destino com o mesmo
  nome, sao ignoradas (lista vazia). Validar manualmente.
- *"Pagamento nao reconciliou"* -> o ``ref`` nao continha
  referencias validas a faturas posted. Verificar formato:
  ``INV/2026/0058, INV/2026/0059``.
- *"Coluna delivery_count missing"* -> o ``_ensure_column`` cria a
  coluna automaticamente. Se falhar, a BD destino nao deu permissoes
  para ALTER TABLE.

g) Pontos de atencao / avisos
-----------------------------
- **Valores HARDCODED a ter sempre em mente**:
  - Nome da BD principal: ``PICCOLO``.
  - Nome da BD destino: ``PICCOLO_COMMUNITY``.
  - ``journal_id = 50`` na BD principal para faturas (apos sync).
  - ``fixed_journal_id = 14`` na BD destino para pagamentos.
  - ``x_studio_volumes_3``, ``x_studio_peso_kg_1``,
    ``x_studio_cubicagem_1``, ``x_studio_zona``,
    ``x_studio_community``, ``x_studio_community_delivery``,
    ``x_studio_observaes_no_recibo`` (typo herdado de Studio - NAO
    renomear sem migration).
- O matching de partner e por ``name`` (case-sensitive). Risco de
  duplicacao se houver clientes com pequenas variacoes ortograficas.
- O matching de taxas e por ``name``. Outra fonte de risco se a
  nomenclatura diverge entre BDs.
- Faz ``cr.commit()`` no meio do fluxo (na BD principal apos mudar
  journal e apos posting) - intencional para garantir que a alteracao
  fica gravada mesmo se a sync da segunda BD falhar. Implica que NAO
  ha rollback total: se falhar a meio, o estado pode ficar
  parcialmente alterado.
- A criacao do produto na BD destino (``_find_or_create_product``)
  usa fallback ``[0]`` para categoria e UoM se nao houver match -
  ficam em categorias/UoMs aleatorios, ha que normalizar a
  posteriori.
- A garantia da coluna ``account_move.delivery_count`` via
  ``_ensure_column`` e DDL fora do ORM - se a BD tiver replicacao,
  validar que o ALTER e propagado.
- ``account_reports.py`` faz ``split("\\n")[0]`` no nome da linha do
  relatorio Aged Receivable. Esconde nomes multi-linha (esperado);
  se o nome legitimo tiver ``\\n``, fica truncado.
""",
    "installable": True,
    "application": False,
}
