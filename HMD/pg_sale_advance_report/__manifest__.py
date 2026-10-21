# -*- coding: utf-8 -*-
{
    'name': 'PG Sale Advance Report',
    'version': '18.0.1.0.0',
    'summary': 'Relatorio PDF de controlo de adiantamentos por encomenda (faturas de adiantamento + sale_advance_payment), com totais.',
    'description': """
PG Sale Advance Report
======================

a) Objetivo de negocio
----------------------
A HMD recebe adiantamentos/depositos (tipicamente 40%) na adjudicacao.
Esses adiantamentos sao registados de DUAS formas: (1) faturas de
adiantamento nativas do Odoo (down payment) e (2) o sistema do modulo
`sale_advance_payment` (pagamentos ligados a encomenda). Faltava um
relatorio unico de controlo. Este modulo gera um relatorio PDF, em
tabela, com uma linha por encomenda com adiantamento e somatorios no
fim.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise.
- Modulos `sale_management`, `account`, `sale_advance_payment`.

c) Como funciona (tecnico)
--------------------------
1. Wizard `sale.advance.report.wizard` (filtros: datas e empresa) ->
   botao Imprimir chama o relatorio QWeb com `data`.
2. `report.pg_sale_advance_report.report_advances._get_report_values`:
   - percorre as `sale.order` confirmadas no periodo;
   - Fonte 1 (faturas de adiantamento): faturas da SO `posted` cujas
     linhas de produto sao TODAS `is_downpayment` (faturas puras de
     adiantamento) -> soma `amount_untaxed` e `amount_total`;
   - Fonte 2 (`sale_advance_payment`): soma dos `account.payment`
     ligados a SO (`account_payment_ids`) nao cancelados;
   - calcula total adiantado, % sobre o total c/IVA e por receber;
   - acumula somatorios globais.
3. Template QWeb `report_advances`: tabela + linha de TOTAIS.
4. Menus em Vendas > Relatorios e Contabilidade > Relatorios.

d) Definicao usada (importante)
-------------------------------
"Adiantamento por fatura" = valor BRUTO das faturas de adiantamento
emitidas (antes da regularizacao/deducao na fatura final). Se for
preciso o valor LIQUIDO por regularizar, ajustar o filtro para somar
as linhas `is_downpayment` (positivas - negativas).

e) Pontos de atencao / avisos
-----------------------------
- Relatorio so-leitura; nao altera dados.
- Carece de confirmacao visual do PDF e de validacao dos numeros
  contra uma encomenda conhecida (nao validavel headless).
- Sem desenvolvimento sobre `vendor/odoo_src`; namespace `pg_`.
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['sale_management', 'account', 'sale_advance_payment'],
    'data': [
        'security/ir.model.access.csv',
        'report/sale_advance_report_templates.xml',
        'report/sale_advance_report.xml',
        'views/sale_advance_report_views.xml',
    ],
    'installable': True,
    'application': False,
}
