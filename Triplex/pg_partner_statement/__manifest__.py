{
    "name": "Extrato Simplificado de Clientes",
    "summary": "Relatório simples de faturação e dívida por cliente num intervalo de datas",
    "version": "17.0.1.0.0",
    "description": """
Extrato Simplificado de Clientes
================================

Objetivo de negócio
-------------------
Obter rapidamente, por cliente e por moeda, um resumo de faturação e dívida num intervalo
de datas: quanto foi faturado (finais e adiantamentos), notas de crédito, o líquido, o que
ficou por pagar do período e o saldo total da conta corrente à data final.

Pré-requisitos
--------------
- Módulos: `account`, `sale`.
- Faturas/notas de crédito lançadas (state = posted) no período a analisar.
- Permissões de acesso ao(s) modelo(s) do extrato (definidas em security/ir.model.access.csv).

Como funciona
-------------
- Assistente `pg.partner.statement.wizard`: recebe intervalo de datas e (opcionalmente)
  clientes; se nenhum cliente for indicado, usa todos os clientes ativos.
- `_compute_invoice_buckets`: soma, por cliente × moeda, faturas finais, faturas de
  adiantamento, notas de crédito e o residual do período. Distingue adiantamentos das
  faturas finais (uma fatura é "adiantamento" só se TODAS as linhas de produto vierem de
  linhas de venda com `is_downpayment`).
- `_compute_balance_buckets`: calcula o saldo da conta corrente (contas a receber em aberto)
  à data final, na moeda do movimento.
- Os resultados são materializados em linhas `pg.partner.statement.line` (modelo transitório)
  para visualização em lista ou impressão em PDF.

Passo a passo de utilização
---------------------------
1. Abrir o menu do Extrato Simplificado de Clientes.
2. Definir "Data de" e "Data até" e, se quiser, selecionar clientes específicos.
3. Carregar em "Ver linhas" para consultar no ecrã, ou "Imprimir PDF" para o relatório.

Exemplo prático
---------------
Intervalo 01/01 a 31/01: para o cliente A em EUR, o extrato mostra Faturas Finais 10.000€,
Adiantamentos 2.000€, Notas de Crédito 500€, Total Líquido 11.500€, Por Pagar do Período
3.000€ e Saldo Total de Conta Corrente 4.200€ (inclui movimentos anteriores).

FAQ / Resolução de problemas
----------------------------
- P: Uma fatura final com dedução de adiantamento aparece onde?
  R: Como fatura FINAL — o seu total já é líquido do adiantamento deduzido.
- P: O "Por Pagar do Período" difere do "Saldo Total".
  R: É esperado: o "Por Pagar do Período" só considera faturas do intervalo; o "Saldo Total"
     inclui também movimentos anteriores à data inicial.
- P: Erro "A data inicial não pode ser posterior à data final".
  R: Corrigir o intervalo de datas no assistente.

Pontos de atenção
-----------------
- Os valores são agrupados por cliente × moeda (multimoeda suportado).
- O extrato é informativo/transitório (não cria movimentos contabilísticos).
""",
    "license": "LGPL-3",
    "author": "Parametro Global",
    "depends": ["account", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/partner_statement_line_views.xml",
        "views/partner_statement_wizard_views.xml",
        "report/partner_statement_report.xml",
        "report/partner_statement_template.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": False,
}
