---
assunto: Fatura FTO/00002 e encontro de contas Jeremias — acção necessária hoje
para: Daniela Martins <daniela.martins@comval.pt>
cc:
bcc:
---

Bom dia, Daniela,

Respondo aos dois pontos que colocou. Começo pelo mais urgente, porque tem prazo hoje: a comunicação do SAF-T de faturação de julho à AT termina no dia 5 do mês seguinte, ou seja, hoje.

**1. Fatura FT FTO/00002 — Jeremias**

A fatura ficou anulada e não é recuperável. Fica com estado fiscal **A — Anulado**, e em Portugal um documento anulado não se reabre nem se reutiliza: o número FTO/00002 fica queimado. Não há aqui nada a corrigir na fatura em si.

O que importa garantir é que a AT fica com a informação certa. Para isso preciso que me confirme uma coisa: **o SAF-T de julho chegou a ser aceite no portal e-Fatura?** No Odoo, o registo do ficheiro de julho está marcado com erro e foi gerado a 3 de agosto às 13:25 — portanto antes de a fatura ter sido anulada, no dia 4.

- **Se ainda não foi aceite:** gere e submeta o SAF-T de julho hoje. O ficheiro novo já leva a FTO/00002 como anulada e não há mais nada a fazer.
- **Se já foi aceite:** gere e submeta novamente o SAF-T de julho. A AT considera apenas a última versão entregue de cada período e não duplica os documentos já comunicados.

Em qualquer dos casos, confirme depois no e-Fatura que a FTO/00002 aparece como anulada.

Se a venda ao Jeremias se mantém, emitimos uma fatura nova, com número novo. **Não emita nota de crédito sobre a FTO/00002:** ela já não tem efeito contabilístico e uma nota de crédito criaria uma segunda reversão indevida. Se o Jeremias já recebeu o PDF da fatura anulada, convém pedir-lhe que a desconsidere.

**2. Encontro de contas de 1 455,03 €**

Os dois pagamentos que criou, PAY00008 e PAY00009, **não geraram qualquer lançamento contabilístico** — é por isso que o valor não aparece na conta corrente. Não houve movimento nenhum, nem contabilístico nem bancário, pelo que podemos cancelá-los sem qualquer impacto.

O encontro de contas não se faz com pagamentos. Faz-se em **Contabilidade → Reconciliar**, e é o Odoo que cria sozinho a transferência entre as contas 221 Fornecedores c/c e 211 Clientes c/c. O procedimento é:

- filtrar pelo parceiro JEREMIAS ESPAÑA SA;
- selecionar a linha a pagar **VFA26050387**, de 1 455,03 € (está no lançamento de saldo inicial SI/2026/08/0017, não numa fatura de fornecedor);
- selecionar as linhas a receber que pretende compensar;
- activar **Permitir parciais**;
- carregar em **Reconciliar**.

Um aviso prático, para não perder tempo: **não existe forma de somar exactamente 1 455,03 € do lado do cliente.** As faturas e saldos em aberto terminam todos em ,00, ,50 ou ,70 e nenhuma combinação dá ,03. A reconciliação vai ficar necessariamente parcial e sobra uma diferença numa das linhas. É normal e não é erro.

A situação em aberto do Jeremias, neste momento, é esta:

| Conta | Documento | Valor |
| --- | --- | --- |
| 221 Fornecedores c/c | VFA26050387 | 1 455,03 a pagar |
| 221 Fornecedores c/c | VFA26060681 | 1 581,05 a pagar |
| 221 Fornecedores c/c | VAB26060023 (nota de crédito) | 87,83 a favor |
| 211 Clientes c/c | Saldos iniciais (7 linhas) | 1 508,70 a receber |
| 211 Clientes c/c | FTO/00009 a FTO/00012 e FTO/00026 | 796,50 a receber |

No total são 2 305,20 € a receber contra 2 948,25 € a pagar. Se preferir, em vez de acertar apenas os 1 455,03 €, podemos compensar a conta corrente toda de uma vez e fica um saldo de 643,05 € a pagar ao Jeremias. Diga-me qual das duas opções corresponde ao que combinou com eles.

Reparei também que o Nuno tinha criado um lançamento manual, o MISC/2026/08/0001, já com a transferência correcta entre as duas contas, e depois cancelou-o. Vale a pena alinharem entre os dois, para não estarem ambos a resolver o mesmo ponto.

**3. Evitar que volte a acontecer**

Sim, dá-se para bloquear, e com configuração standard do Odoo — não é preciso desenvolvimento. Chama-se **Datas de Bloqueio**: fechando as vendas até 31/07, o Odoo passa a recusar cancelar ou alterar qualquer documento com data anterior a essa. Confirmámos que era exactamente isto que teria impedido este cancelamento.

A minha proposta é fecharmos julho **assim que o SAF-T de julho estiver aceite**, e não antes — para não bloquearmos correcções que ainda possam ser necessárias neste período. A partir daí passa a ser um hábito mensal: submeter o SAF-T e fechar o mês.

**O que preciso de si**

Ligo-lhe hoje de manhã para confirmarmos o estado do SAF-T de julho e fazermos o encontro de contas em conjunto no Reconciliar — são poucos cliques, mas é mais rápido acompanhado. Diga-me apenas a que horas lhe é mais conveniente.
