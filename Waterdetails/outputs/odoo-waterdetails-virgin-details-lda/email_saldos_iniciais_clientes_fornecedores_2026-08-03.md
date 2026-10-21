---
assunto: Instruções — lançamento de saldos iniciais de clientes e fornecedores — Waterdetails
para: Daniela Martins <daniela.martins@comval.pt>
cc:
bcc:
---

Bom dia, Daniela,

Como os saldos em aberto são poucos, podem ser lançados manualmente no Odoo, sem necessidade de preparar um ficheiro Excel. Para manter o detalhe das contas correntes, recomendamos criar uma linha por documento em aberto, indicando o contacto, a referência, a data de vencimento e o respetivo valor.

O lançamento deve ser efetuado em **Contabilidade → Contabilidade → Lançamentos de Diário → Novo**, utilizando o diário **Saldo inicial**. Para facilitar a validação, sugerimos criar um lançamento para clientes e outro para fornecedores.

Na grelha dos Itens do Diário, o campo correspondente ao contacto chama-se **Parceiro**. A coluna **Data de vencimento** já se encontra disponível, permitindo indicar a data de vencimento original de cada documento. A opção **Deferred Date** não corresponde à data de vencimento e não deve ser utilizada para este efeito.

**Saldos de clientes**

Em cada documento em aberto, criar uma linha com:

- o cliente no campo Parceiro;
- a conta **211 — Clientes c/c**;
- a referência da fatura no campo Descrição;
- a data de vencimento;
- o valor em **Débito**.

No final, criar uma linha de contrapartida na conta **999999**, com o total em **Crédito**.

**Saldos de fornecedores**

Em cada documento em aberto, criar uma linha com:

- o fornecedor no campo Parceiro;
- a conta **221 — Fornecedores c/c**;
- a referência da fatura no campo Descrição;
- a data de vencimento;
- o valor em **Crédito**.

No final, criar uma linha de contrapartida na conta **999999**, com o total em **Débito**.

No exemplo enviado, se os 437,88 € da fatura `FT R2024/53` correspondem a um valor que o cliente ainda deve pagar, os montantes devem ser invertidos: os 437,88 € ficam em **Débito** na conta **211 — Clientes c/c** e em **Crédito** na conta **999999**. A disposição apresentada na imagem só deve ser usada quando existe um saldo a favor do cliente.

Antes de publicar cada lançamento, confirmar que o total a débito é igual ao total a crédito e que o total das contas correntes coincide com a listagem do sistema anterior. Não é necessário recriar as faturas antigas no Odoo; estes movimentos servem para registar os valores que continuam em aberto e permitir a respetiva reconciliação quando os pagamentos forem recebidos ou efetuados.

Se surgir alguma dúvida durante o lançamento, basta ligar-nos e fazemos uma reunião rápida para explicar o processo e acompanhar os primeiros registos.
