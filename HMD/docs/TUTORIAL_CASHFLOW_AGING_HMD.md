# Tutorial — Tesouraria: antiguidade de saldos e fluxo de caixa (HMD)

> Como usar os relatórios financeiros do Odoo para ver **quem deve e a quem se
> deve** (com prazos 30/60/90) e o **fluxo de caixa**. Os relatórios já estão
> disponíveis (módulo `account_reports` instalado).
> Serve também de guião para o vídeo curto HMD-specific.

## Onde estão

Tudo em **Contabilidade → Relatórios** (*Accounting → Reporting*). Os que
interessam para tesouraria são:

| Relatório | Para quê |
|---|---|
| **Antiguidade de Saldos a Receber** (*Aged Receivable*) | Quanto cada **cliente** deve e há quanto tempo (30/60/90+) |
| **Antiguidade de Saldos a Pagar** (*Aged Payable*) | Quanto se deve a cada **fornecedor** e há quanto tempo |
| **Demonstração de Fluxos de Caixa** (*Cash Flow Statement*) | Entradas e saídas de caixa do período |
| **Relatório de Seguimento** (*Follow-Up Report*) | Gestão de cobranças a clientes |

---

## 1. Antiguidade de Saldos a Receber (o mais usado)

**Contabilidade → Relatórios → Antiguidade de Saldos a Receber.**

O que vês:
- Uma linha por **cliente**, com o saldo distribuído por **colunas de prazo**:
  *Não vencido*, *0–30*, *31–60*, *61–90*, *90+* dias.
- O total em dívida e o que já está **em atraso**.

Como usar:
1. Confirma a **data** no topo (a antiguidade é calculada a essa data).
2. **Expande** um cliente para ver as faturas que compõem o saldo.
3. Usa para priorizar **cobranças**: foca as colunas 60/90+.

> Dica: clica numa célula para ver o detalhe (drill-down) até à fatura.

---

## 2. Antiguidade de Saldos a Pagar

**Contabilidade → Relatórios → Antiguidade de Saldos a Pagar.**

Igual ao anterior, mas para **fornecedores**: quanto se deve e com que prazo.
Serve para **planear pagamentos** e antecipar saídas de caixa.

---

## 3. Demonstração de Fluxos de Caixa

**Contabilidade → Relatórios → Demonstração de Fluxos de Caixa.**

Mostra as **entradas e saídas de caixa** do período (operacional, investimento,
financiamento). Usa para perceber a **variação de tesouraria** num intervalo.

- Escolhe o **período** no topo (mês, trimestre, intervalo personalizado).
- **Compara períodos** para ver a evolução.

---

## 4. Ferramentas comuns a todos os relatórios

No topo de cada relatório tens:
- **Datas / Período** — definir o intervalo ou a data de referência.
- **Comparar** — período homólogo ou anterior.
- **Exportar** — para **PDF** ou **Excel** (botão de exportação).
- **Guardar como favorito** — guardar a configuração para reabrir com um clique.

---

## 5. Gestão de cobranças (Follow-Up)

**Contabilidade → Clientes → Seguimento de Pagamentos** (*Follow-up*):
- Lista os clientes com valores em atraso e o **nível de lembrete** a enviar.
- Permite **enviar lembretes** (email) e registar o contacto feito.

---

## Boas práticas

- **Rotina semanal:** abrir a *Antiguidade a Receber*, atacar as colunas 60/90+.
- **Antes de pagar fornecedores:** cruzar a *Antiguidade a Pagar* com a posição
  de caixa.
- **Fecho de mês:** exportar os relatórios (PDF/Excel) para arquivo.
- **Tudo standard:** estes relatórios são nativos do Odoo (sem programação) e
  atualizam em tempo real a partir da contabilidade.

---

## Resumo em 3 linhas

1. **A Receber / A Pagar** (antiguidade 30/60/90) → quem deve e a quem se deve.
2. **Fluxo de Caixa** → entradas e saídas do período.
3. **Datas + Comparar + Exportar** em todos; **Follow-Up** para cobranças.
