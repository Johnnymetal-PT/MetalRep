# -*- coding: utf-8 -*-
{
    'name': 'PG Account Report Enhancements',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Acrescenta a coluna "Days Overdue" (dias em atraso) aos relatorios Aged Partner Balance e Partner Ledger.',
    'author': 'Parametro Global',
    'depends': ['account_reports'],
    'data': [
        'views/account_aged_report_extension.xml',
        'views/account_partner_ledger_extension.xml',
    ],
    'description': """
PG Account Report Enhancements
==============================

a) Objetivo de negocio
----------------------
Permitir ao financeiro/cobrancas perceber, sem calcular manualmente, ha
quantos dias cada fatura esta vencida nos relatorios Aged Receivable,
Aged Payable e Partner Ledger.

b) Pre-requisitos
-----------------
- Modulo Enterprise ``account_reports`` instalado.
- Sem campos Studio, sem bibliotecas externas.
- Datas de fatura preenchidas (``invoice_date``) - se vazias o valor da
  coluna fica em branco.

c) Como funciona
----------------
- Estende dois handlers AbstractModel do core Enterprise:
  - ``account.aged.partner.balance.report.handler``
    (``models/account_aged_report_handler.py``)
  - ``account.partner.ledger.report.handler``
    (``models/account_partner_ledger_handler.py``)
- Override do metodo `_aged_partner_report_custom_engine_common` (Aged) e
  `_custom_partner_ledger_report_engine` (Partner Ledger): apos chamar
  super(), injecta a chave ``days_overdue`` em cada linha do resultado,
  calculada como ``date.today() - invoice_date``.
- Override de ``_prepare_partner_values`` para inicializar
  ``days_overdue=None`` e evitar KeyError nas linhas sem fatura.
- Define em XML uma coluna ``account.report.column`` e uma
  ``account.report.expression`` ``days_overdue`` em cada relatorio,
  ligadas ao engine custom de cada um.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Contabilidade > Reporting > Aged Receivable / Aged Payable.
3. Verificar a coluna "Days Overdue" - e ordenavel.
4. Mesmo passo para Partner Ledger.

e) Exemplo pratico
------------------
Fatura ``INV/2026/0123`` com ``invoice_date = 2026-04-01``, data atual
``2026-05-28`` -> coluna "Days Overdue" = ``57``.
Linha agregada do partner mostra o valor da fatura individual mais antiga.

f) FAQ / Resolucao de problemas
-------------------------------
- *"A coluna nao aparece"* -> confirmar que ``account_reports`` esta
  instalado (Enterprise) e que o modulo esta na lista de Apps com
  estado "Installed".
- *"Coluna a vazio"* -> a fatura nao tem ``invoice_date``; preencher na
  fatura ou ignorar (linhas agregadas ficam None propositadamente).
- *"KeyError days_overdue"* -> normalmente significa que existia uma
  versao parcial; reinstalar/atualizar este modulo aplica o override de
  ``_prepare_partner_values`` que evita o erro.

g) Pontos de atencao / avisos
-----------------------------
- IDs XML usados: ``pg_account_aged_receivable_days_overdue_column``,
  ``pg_account_aged_payable_days_overdue_column``,
  ``pg_partner_ledger_days_overdue_column`` - manter o prefixo ``pg_``
  para nao colidir com IDs do core ao fazer upgrade do Odoo.
- Os logs ``_logger.info("Final Summary Result: %s", results)`` ficaram
  do desenvolvimento. Sao verbose; em producao podem ser silenciados
  configurando o nivel do logger ``pg_account_reports``.
""",
    'installable': True,
}
