# -*- coding: utf-8 -*-
{
    "name": "PG Account Intrastat HS Code (linha)",
    "summary": "Código HS (commodity code) editável ao nível da linha da fatura.",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://www.parametroglobal.com",
    "category": "Accounting",
    "license": "LGPL-3",
    "description": """
PG Account Intrastat HS Code (HMD) — tarefa 5734
================================================

Adiciona o código HS (commodity code) à linha da fatura
(`account.move.line.pg_intrastat_code_id`), a par dos campos Intrastat
standard já existentes na linha ("Intrastat" e "País do Produto").

- O campo herda por defeito o código HS do produto
  (`product.product.intrastat_code_id`) e é editável/sobreponível por linha.
- Aparece na lista e no formulário das linhas da fatura.

Edição em faturas publicadas
----------------------------
Na view base, `invoice_line_ids` fica readonly quando a fatura está
publicada. Para permitir editar apenas os campos Intrastat (Intrastat,
País do Produto e Código HS) numa fatura confirmada — sem desbloquear
preço/conta/quantidade — adiciona-se a aba "Intrastat" com um One2many
dedicado (`pg_intrastat_line_ids`) cuja lista só expõe esses 3 campos como
editáveis (produto só-leitura, sem criar/apagar linhas). A escrita destes
campos numa move publicada é permitida pelo standard (sujeita à data de
bloqueio fiscal nos 2 campos Intrastat nativos).

NOTA: a declaração Intrastat oficial continua a ler o código HS do produto.
Fazer este campo de linha alimentar a declaração exige override do SQL do
relatório (`account_intrastat`) e é âmbito separado (a confirmar).
""",
    "depends": ["account_intrastat"],
    "data": [
        "views/account_move_views.xml",
    ],
    "installable": True,
    "application": False,
}
