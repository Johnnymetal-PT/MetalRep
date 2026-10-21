# -*- coding: utf-8 -*-
{
    'name': 'PG JASMIN integração',
    'version': '17.0.1.0.0',
    'summary': 'Integracao com o JASMIN Software (Primavera) via REST API: replica faturas, faturas-recibo, faturas simplificadas, notas de credito e guias de transporte; descarrega PDF certificado e anexa ao documento Odoo.',
    'description': """
PG Jasmin Integration
=====================

a) Objetivo de negocio
----------------------
A Piccolo emite documentos fiscais certificados (Fatura, Fatura-Recibo,
Fatura Simplificada, Nota de Credito e Guia de Transporte) atraves do
**JASMIN Software (PRIMAVERA)** - o Odoo nao e certificado. Este modulo
faz a ponte: quando uma fatura/picking e confirmado no Odoo, o
respetivo documento e criado no JASMIN, o PDF certificado e
descarregado e anexado ao registo Odoo.

b) Pre-requisitos
-----------------
- Conta JASMIN ativa com tenant e org keys.
- Credenciais OAuth2 (``client_id`` / ``client_secret``).
- Codigos de documento configurados em JASMIN:
  - Fatura (jas_ft)
  - Fatura-Recibo (jas_fr)
  - Fatura Simplificada (jas_fs)
- Modulos Odoo: ``point_of_sale``, ``sale_stock``, ``sale_management``,
  ``account``, ``sale_subscription``.
- Acesso de saida (HTTPS) para:
  - ``https://identity.primaverabss.com/connect/token`` (auth)
  - ``https://my.jasminsoftware.com/api`` (REST)

c) Como funciona
----------------
- **Configuracao da company** (``models/res_company.py``):
  Campos ``jas_company``, ``jas_username``, ``jas_password``,
  ``jas_tenant_key``, ``jas_org_key``, ``jas_ft``, ``jas_fr``,
  ``jas_fs``. Expostos em Definicoes via ``res_config_settings.py``.

- **JASConnection** (``models/jas_connection.py``):
  Wrapper REST que autentica (``client_credentials``) e expoe metodos
  para o ciclo de vida do documento:
  - ``authenticate``, ``country_exists``, ``iva_code``
  - ``client_exists_or_create`` / ``product_exists_or_create``
  - ``post_invoice`` / ``get_invoice`` / ``get_invoice_print_id``
  - ``post_refund`` / ``get_refund`` / ``get_refund_print_id``
  - ``try_create_sale`` / ``try_create_refund``
  - Helpers ``convert_to_json_partner`` / ``..._product`` /
    ``..._docs`` / ``..._docsRefund`` para formatar payloads.

- **Sincronizacao da fatura** (``models/account_move.py``):
  - Campo ``is_jas_synced`` marca documentos ja replicados.
  - ``connect_jas_and_sync_invoice``: chama ``try_create_sale`` ou
    ``try_create_refund`` conforme o ``move_type`` e a politica de
    documento.
  - **Disparo automatico**: override de ``_post`` em ``account.move``;
    qualquer fatura de venda postada e replicada para o JASMIN
    automaticamente.
  - Botao ``action_sync_to_erp`` permite resync manual.
  - ``add_jas_pdf_to_attachment`` anexa o PDF descarregado ao
    ``ir.attachment`` do documento, escreve em ``jas_invoice`` e
    devolve action que abre o PDF na browser.

- **Guias de transporte** (``models/stock_move.py``):
  - Campos ``is_jas_synced``, ``jas_invoice`` em ``stock.picking``.
  - ``action_print_with_jasmim``: envia dados do picking para
    ``/shipping/deliveries`` em JASMIN; descarrega PDF e anexa ao
    picking. ``documentType = 'GT'``, template
    ``SHIPPING_DELIVERYREPORT_PICCOLO``.

- **POS** (``models/pos_order.py``):
  - Acrescenta ``payment_method_id`` em ``pos.order`` para podermos
    distinguir tipos de pagamento (numerario vs cartao) ao escolher
    o ``documentType`` JASMIN (FS para <= 100EUR, FR para > 100EUR).

- **Anexo do PDF no email** (``wizard/account_move_send.py``):
  Override de ``account.move.send`` que substitui o PDF gerado pelo
  Odoo pelo PDF certificado descarregado do JASMIN no
  ``invoice_pdf_report_file`` antes de enviar ao cliente.

- **Logica de seleccao do documento JASMIN**:
  - ``move_type == 'out_refund'`` -> ``try_create_refund`` (Nota de
    Credito).
  - Caso contrario:
    - Se vem do POS (``move.pos_order_ids``):
      - Total > 100 -> usa ``company.jas_fr`` (Fatura-Recibo)
      - Total <= 100 -> usa ``company.jas_fs`` (Fatura Simplificada)
    - Se nao vem do POS -> usa ``company.jas_ft`` (Fatura).

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Definicoes > Empresas > preencher campos JASMIN
   (Empresa, Utilizador, Autorizacao, Chaves, codigos de documento).
3. Confirmar fatura/picking no Odoo: a replicacao para JASMIN e
   automatica via override de ``_post``.
4. Para resync manual, botao "Sync to ERP" no header da fatura.
5. Para guia de transporte, botao "Print Jasmim Document" no picking.
6. Quando se envia email da fatura ao cliente, e ja o PDF certificado
   JASMIN que vai como anexo.

e) Exemplo pratico
------------------
``INV/2026/0058`` confirmada para "Hotel XYZ" - 3 cadeiras
totalizando 1.250 EUR:
1. ``_post`` posta a fatura no Odoo.
2. Override deteta ``journal_id.type == 'sale'`` -> chama
   ``connect_jas_and_sync_invoice``.
3. ``try_create_sale`` valida ou cria pais/cliente/produto em JASMIN.
4. POST ``/billing/invoices`` cria a fatura em JASMIN (``documentType
   = company.jas_ft``).
5. GET ``/billing/invoices/{id}/print`` descarrega o PDF certificado.
6. PDF anexado a INV/2026/0058 (``jas_invoice``); ``is_jas_synced =
   True``; ``doc_jasmin`` guarda o naturalKey (ex.: ``FT 2026/12``).

f) FAQ / Resolucao de problemas
-------------------------------
- *"Configure as definicoes: Empresa/Utilizador/..."* -> falta algum
  campo na company. Definicoes > Empresas.
- *"Erro ao criar pais: ..."* -> codigo de pais do cliente nao existe
  em JASMIN. Verificar ``res.country.code`` (ISO2).
- *"Erro ao criar iva: ..."* -> taxa do produto nao mapeia para o
  schema fiscal default em JASMIN. Validar diretamente em JASMIN.
- *"PDF nao abre no email"* -> ``jas_invoice`` esta vazio. Reabrir a
  fatura no Odoo e clicar "Sync to ERP".
- *"Documento criado em JASMIN mas Odoo nao marca synced"* -> a
  resposta JASMIN veio com erro tardio; verificar logs do
  ``pg_jasmin_integration`` (varios ``_logger.error`` deixados
  intencionalmente).

g) Pontos de atencao / avisos
-----------------------------
- **Valores HARDCODED criticos** (procurar em jas_connection.py):
  - ``IncomeAccount = "71111"`` para todos os produtos criados em
    JASMIN (sales_extension_data).
  - ``ItemTaxSchema = "NORMAL"`` para os produtos.
  - ``customerGroup`` default = ``"01"`` (cliente nacional);
    fiscal_position ``id = 3`` muda para ``"04"`` (CONTINENTE-UE).
  - ``BaseUnit`` default = ``"UN"`` se a UoM Odoo nao mapear
    (m2 -> M2, m3 -> M3, Horas -> HR).
  - Bearer token e renovado a cada instanciacao de ``JASConnection``
    (ineficiente; aceitavel para volume Piccolo).
- **Override do ``_post``**: TODA fatura de venda postada e enviada
  para JASMIN, mesmo as importadas em batch. Se nao for desejado em
  algum cenario, desligar via ``with_context(skip_jasmin=...)`` (nao
  implementado - tem de ser acrescentado).
- **Re-sync nao e idempotente**: chamar ``Sync to ERP`` numa fatura
  ja sincronizada cria DUAS faturas em JASMIN. Garantir
  ``is_jas_synced`` antes de re-executar manualmente.
- **POS**: a logica de FS/FR depende de ``self.pos_order_ids`` e do
  total das linhas - se houver caso de uso de POS sem ``pos_order_ids``
  preenchido, valida a logica.
- **typos/erros no JASMIN** sao re-lancados como ``ValidationError``
  ao utilizador - alguns sao misleading (ex.: ``Error_msg`` em
  ``try_create_sale`` so deteta dict, nao deteta string).
- **Stock move payload** (``prepare_delivery_payload``) tem o campo
  ``company`` HARDCODED a ``"PICCOLO"`` em vez de
  ``jas_connection.company``. **Bug a confirmar** se a Piccolo tiver
  mais que uma company JASMIN.
- ``stock_move.py`` re-instancia ``JASConnection`` em vez de
  reutilizar a do contexto. Aceitavel; tem custo de auth extra.
""",
    'category': 'Accounting',

    'author': 'PG',
    'website': 'https://www.parametro.pt',

    'depends': ['point_of_sale', 'sale_stock', 'sale_management', 'account', 'sale_subscription'],

    'assets': {
        'point_of_sale._assets_pos': [
            'pg_jasmin_integration/static/src/**/*',
        ],
    },
    'data': [
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
