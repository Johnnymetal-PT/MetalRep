# Editar um orçamento já aceite e propagar as alterações à encomenda

- **Tarefa:** #7788
- **Para:** reunião geral de 15/10/2026
- **Data:** 13/10/2026
- **Versão:** 1.0 (rascunho para integrar no guião, secção 7)
- **Base:** produção HMD, leitura de 13/10/2026 (nada foi alterado); ensaios da Lara no ambiente de teste a 09 e 10/10

---

## 1. O que a HMD pediu

Às vezes o cliente aceita o orçamento e até paga uma parte, mas depois pede para alterar alguma coisa. A HMD quer poder editar o orçamento e que as alterações (preço e outras) passem também para os outros documentos dessa encomenda.

## 2. O que a certificação permite

A Autoridade Tributária não permite alterar documentos já emitidos. Com a certificação da Exo (ptplus), o orçamento e a encomenda confirmados ficam fixos. A documentação da Exo para o Odoo 18 diz o mesmo e indica três caminhos de correção:

| Situação | O que a Exo prevê |
|---|---|
| Orçamento ainda em rascunho | Edita-se à vontade |
| Orçamento emitido | Já não se edita; faz-se uma **nova revisão** (módulo «Portugal - Sale Order Revisions») |
| Fatura emitida | Corrige-se por **nota de crédito** (ou de débito), emitida a partir da própria fatura |

A documentação não descreve nenhum procedimento de anulação ou de refaturação de documentos certificados, e não diz como tratar uma encomenda já confirmada com documentos ligados. Fonte: documentação da Exo, página «odoo_process» (Odoo 18).

Há um ponto a esclarecer com a Exo: o módulo de revisões de orçamentos existe no catálogo da base da HMD («Portugal - Sale order version»), mas está marcado como **não instalável** na versão 18. Não sabemos se a Exo o tem para a nossa versão.

## 3. O que o Odoo faz hoje, comprovado

Ensaio da Lara em teste (encomenda NE A/00118 com adiantamento FT A/00086), confirmado com o código do Odoo 18:

| Ação | Resultado | Porquê |
|---|---|---|
| Alterar preço ou acrescentar linha | Bloqueado | Documento emitido |
| Voltar a orçamento | Bloqueado | Documento emitido |
| Cancelar a encomenda | Permitido, mesmo com adiantamento faturado | O cancelamento standard só impede encomendas bloqueadas |
| Duplicar a encomenda cancelada | Dá um orçamento novo, editável (S01278), que se confirma como NE A/00137 | Cópia standard |

**O que o cancelamento faz aos documentos ligados** (código standard `sale`, `sale_stock`, `sale_purchase`):

| Documento ligado | O que acontece ao cancelar a encomenda |
|---|---|
| Entregas não concluídas | Cancelam-se sozinhas |
| Entregas já concluídas | Ficam como estão |
| Faturas em rascunho | Cancelam-se sozinhas |
| Faturas emitidas (adiantamento) | **Ficam na encomenda cancelada**, sem ligação à nova |
| Compras (pedidos a fornecedores) | **Não se cancelam**; o Odoo cria uma atividade de aviso («Exception») na compra. Ensaio de 13/10: aconteceu também com um artigo físico, e a receção associada cancelou-se sozinha |
| Ordens de produção | **Não se cancelam** (confirmado no ensaio: OP/06461 ficou em rascunho) |

## 4. Quanto isto pesa na HMD

Produção, 13/10/2026:

| O que medimos | Valor |
|---|---|
| Encomendas confirmadas | 64 |
| Dessas, com linha de adiantamento | 27 |
| Dessas, com pelo menos uma entrega concluída | 23 |
| Compras confirmadas ligadas a encomendas confirmadas | 59 |
| Ordens de produção abertas ligadas a encomendas confirmadas | 76 |
| Encomendas já canceladas | 33 (nenhuma tem compras nem ordens de produção ligadas) |

Duas leituras:

- Quase todas as encomendas confirmadas têm compras e ordens de produção. Alterar uma encomenda aceite quase sempre obriga a rever esses documentos.
- Em 23 encomendas já houve entrega. O circuito de cancelar e refazer só serve **antes da entrega**; depois disso, cancelar não desfaz o que já saiu.

## 5. Proposta de circuito para 15/10

Sem desenvolvimento: configuração e procedimento do Odoo standard, o mesmo que a Lara ensaiou, completado com os passos que faltavam.

| Passo | Quem | O que se faz |
|---|---|---|
| 1 | Comercial | Confirmar se já houve entrega. Se sim, este circuito não serve (ver secção 6). |
| 2 | Comercial | Se a encomenda estiver bloqueada, desbloqueá-la; depois **cancelar a encomenda**. As entregas por concluir cancelam-se sozinhas. |
| 3 | Compras | Abrir o botão «Purchase Orders» da encomenda cancelada e **cancelar à mão** as compras (as confirmadas também se cancelam no Odoo, e a receção cancela-se sozinha). Se a compra já foi confirmada ao fornecedor, avisá-lo primeiro. Se não se cancelar, a encomenda nova gera uma segunda compra igual. |
| 4 | Produção | Abrir o botão «Manufacturing Orders» e **cancelar à mão** as ordens que ainda não arrancaram. |
| 5 | Comercial | **Duplicar** a encomenda cancelada, alterar o orçamento novo, enviar e confirmar. Recebe nova numeração. |
| 6 | Contabilidade | Na fatura do adiantamento da encomenda antiga, **«Adicionar nota de crédito»**, e validá-la. |
| 7 | Comercial | Na encomenda nova, criar o novo adiantamento (valor fixo igual ao já pago), validar a fatura e, nela, **aplicar a nota de crédito** como crédito pendente. |
| 8 | Comercial | Na fatura final, «Fatura normal» com «Deduzir adiantamentos»: deduz só o adiantamento novo. |
| 9 | Comercial | Registar no chatter da encomenda antiga a referência da nova, e vice-versa. |

Os botões de compras e ordens de produção do passo 3 e 4 já existem na venda (módulo `pg_sale_purchase_link`).

## 5.1 Ensaio de 13/10 na base de testes (HMD_TESTE)

Repetimos o caso de ponta a ponta, com o cliente «Cliente Ensaio Lara» e o artigo CONGO 90 (3 000 € + IVA 23 %). O cliente aceita, paga um adiantamento, e depois o preço sobe para 3 200 €.

**Caminho A — cancelar, nota de crédito, nova encomenda. Funcionou até ao fim.**

| Documento | Valor | Estado final |
|---|---|---|
| NE A/00138 (original, 3 690 €) | 3 690 € | Cancelada; a entrega cancelou-se sozinha |
| FT A/00087 (adiantamento 30 %) | 1 107 € | Validada e paga; mantém-se no livro |
| NC A/00027 (nota de crédito à FT A/00087) | −1 107 € | Validada; **fica como crédito em aberto do cliente**, não se reconcilia sozinha com o adiantamento |
| NE A/00139 (nova, 3 936 €) | 3 936 € | Confirmada; duplicar não traz linhas de adiantamento da antiga |
| FT A/00088 (novo adiantamento) | 1 107 € | Validada e **liquidada com a NC A/00027** (sem mexer no dinheiro do cliente) |
| FT A/00089 (fatura final) | 2 829 € | Validada; deduz só a FT A/00088 (linha −900 € + IVA) |

Contas certas: o cliente pagou 1 107 € uma vez, e deve 2 829 € na fatura final; no total 3 936 €. A FT A/00087 e a NC A/00027 anulam-se e ficam ambas no SAF-T. O ptplus não pediu campos novos na nota de crédito (só motivo e diário) e aceitou todos os documentos.

**Caminho C — não cancelar; corrigir o preço só na fatura final. Funciona, mas não é o que a HMD pediu.**
- Alterar o preço na encomenda confirmada foi recusado pelo ptplus: «É proibido modificar os seguintes campos de um documento emitido: Unit Price».
- Na fatura final em rascunho o preço pôde ser alterado, e a fatura foi validada com 2 829 € (3 936 € − 1 107 €).
- Resultado: a encomenda NE A/00140 continua a 3 690 € e a faturação soma 3 936 €. O documento aceite deixa de bater com o faturado, e as compras e ordens de produção não são atualizadas. **Não recomendamos**: é um desvio entre documentos que um auditor ou a AT podem questionar.

## 5.2 Ensaios de 13/10: compra confirmada, entrega concluída e SAF-T

**Compra já confirmada ao fornecedor (artigo com rotas «Comprar» e «Sob encomenda»).**
- Ao confirmar a venda nasceu a compra P00960 em rascunho; confirmada, passou a «Ordem de compra» e criou a receção HMD/IN/00635.
- Cancelar a venda **não cancelou a compra**: ficou confirmada, com uma atividade «Exception — manual actions may be needed». A receção e a entrega cancelaram-se sozinhas.
- Duplicar e confirmar a encomenda nova criou **uma segunda compra** (P00961), igual à primeira.
- Cancelar a P00960 à mão funcionou (a compra passou a «Cancelada»). O Odoo não obrigou a nenhum passo extra.
- Conclusão: o passo 3 do circuito é necessário e funciona. Sem ele a HMD compra duas vezes ao fornecedor.

**Entrega já concluída.**
- Com a entrega validada (GT A/00098, guia de transporte certificada), cancelar a venda foi **permitido**, e a guia ficou como «feita».
- No SAF-T, a guia GT A/00098 aparece com estado normal e referencia a NE A/00143 (`OriginatingON`), que o mesmo ficheiro dá como **anulada**. É uma inconsistência fiscal: a mercadoria saiu contra uma encomenda anulada.
- Uma encomenda nova duplicada voltaria a gerar a entrega e a pedir a mercadoria outra vez.
- Conclusão: **depois da entrega não se deve cancelar a encomenda**. O circuito só serve antes de qualquer guia de transporte. Para alterações depois da entrega propomos uma encomenda complementar só para a diferença, ou, se for erro de preço, nota de crédito à fatura e nova fatura (INFERÊNCIA; não ensaiámos este último caso, por depender da contabilista).

**SAF-T de faturação (13/10, só ensaios, sem marcar o período como reportado).**

| Documento | Como sai no SAF-T |
|---|---|
| FT A/00087 (adiantamento original) | Estado normal, com ATCUD e hash |
| NC A/00027 | Estado normal; a linha **referencia a FT A/00087**; fecha o adiantamento original |
| FT A/00088 e FT A/00089 | Normais; a final deduz só a A/00088 |
| NE A/00138 (cancelada) | Estado **«A» (anulada)** |
| NE A/00139 (nova) | Estado normal, 3 936 € |
| NE A/00140 e FT A/00091 (caminho C) | A encomenda diz 3 690 € e a fatura traz a linha a 3 200 €: o desvio vê-se no ficheiro |

Conclusão fiscal: o caminho A produz um ficheiro coerente (documento anulado, nota de crédito ligada à fatura, documentos novos normais). O caminho C deixa uma incoerência entre encomenda e fatura. Nota técnica: a primeira tentativa de exportação pelo botão «Exportar» falhou com um erro do ptplus (`_render_invoices`, valor vazio onde se esperava texto) e a segunda, por «Export XML», funcionou. Não investigámos a causa; convém perguntar à Exo se se repete em produção.

**O que pesa na escolha**

| | A: cancelar + nota de crédito + nova encomenda | C: corrigir só a fatura final |
|---|---|---|
| Fiscal | Limpo: nenhum documento emitido é alterado, cada correção é um documento novo e ligado | Desvio entre encomenda e fatura |
| Atualiza compras e ordens de produção | Sim, ao refazer a encomenda | Não |
| Passos para o utilizador | 9, mas todos botões standard; o crédito aplica-se com um clique | 1 (mas só serve para preço) |
| Serve para alterar quantidades ou artigos | Sim | Não |

**Conclusão do ensaio:** o caminho A é o melhor fiscalmente e o único que cumpre o pedido; é mais longo, mas todos os passos são botões do Odoo. Os passos que mais pesam são o 3 e o 4 (compras e ordens de produção à mão) e o 6 a 8 (adiantamento). É aqui que um botão guiado ajudaria mais, e não na encomenda em si.

Documentos de ensaio, todos marcados «ZZ TESTE 7788» na referência do cliente: encomendas 1280 (NE A/00138), 1281 (NE A/00139) e 1282 (NE A/00140). As faturas validadas não se apagam.

## 6. O que fica por decidir

| Ponto | Opções | Quem decide |
|---|---|---|
| **Adiantamento já faturado.** A fatura fica na encomenda cancelada e a fatura final da nova encomenda não a consegue deduzir. | Ensaiado: nota de crédito ao adiantamento, novo adiantamento na encomenda nova, liquidado com a nota de crédito (secção 5.1). Funcionou. | Contabilista da HMD confirma o tratamento contabilístico; Exo confirma que é o procedimento certo |
| **Encomendas com entrega já feita.** O circuito não serve: ensaiado, deixa uma guia de transporte a referenciar uma encomenda anulada. | Encomenda complementar só para a diferença; ou, se for erro de preço, nota de crédito e nova fatura (por ensaiar) | HMD e contabilista |
| **Compras já confirmadas ao fornecedor.** O Odoo cancela-as à mão sem problema, mas não sozinho. | Avisar o fornecedor e cancelar; ou, se só mudou o preço de venda, manter a compra (e a encomenda nova não deve gerar outra) | Compras da HMD |
| **Automatizar os passos 3, 4 e 7?** Um botão «Rever encomenda» que cancela, duplica e avisa do que ficou aberto. É customização leve. | Só depois de a HMD usar o procedimento manual algumas vezes | Lara, com a Nina |

## 7. Pontos por validar

- [ ] Perguntar à Exo se o módulo «Portugal - Sale Order Revisions» existe para o Odoo 18 e se serve para encomendas já confirmadas. A versão base (OCA) só cria revisões a partir de encomendas **canceladas**, que é o que o circuito acima já faz. Ganhava-se a numeração da revisão e o histórico de versões.
- [ ] Confirmar com a Exo e com a contabilista da HMD o tratamento do adiantamento (nota de crédito ao adiantamento). O ensaio mostra que o Odoo e o ptplus aceitam; falta dizer se é o que a contabilidade quer.
- [x] ~~Confirmar que o novo orçamento duplicado não herda linhas de adiantamento da encomenda antiga.~~ Confirmado a 13/10: não herda.
- [x] ~~Ensaiar em teste o caso com compra confirmada e o caso com entrega concluída.~~ Feito a 13/10 (secção 5.2).
- [x] ~~Rever o SAF-T do período de teste.~~ Feito a 13/10 (secção 5.2): FT A/00087 e NC A/00027 saem ligadas; encomenda cancelada sai como anulada.
- [ ] Perguntar à Exo porque falhou a exportação SAF-T pelo botão «Exportar» (e funcionou por «Export XML»).
- [ ] Decidir com a contabilista o que fazer depois de uma guia de transporte emitida.
- [ ] Evitar o segundo pedido ao fornecedor: avaliar se a encomenda nova pode reutilizar a compra já confirmada (hoje cria outra).

## 8. Referências

- Documentação da Exo (Odoo 18): `https://github.com/exosoftware/documentation/blob/18.0/content/applications/invoicing/odoo_process.rst`
- Módulo base das revisões (OCA): `https://github.com/OCA/sale-workflow/tree/18.0/sale_order_revision`
- Código do Odoo 18 consultado: `addons/sale/models/sale_order.py` (`action_cancel`, `_action_cancel`), `addons/sale_stock/models/sale_order.py` (`_action_cancel`), `addons/sale_purchase/models/sale_order.py` (`_action_cancel`), em `C:\Users\Utilizador\.pg\odoo_src\18.0\community\addons\`
- Módulos da HMD: `pg_sale_purchase_link`, `ptplus_sale_advance_payment`, `sale_advance_payment`
- O código do ptplus não está acessível; o que se afirma sobre ele vem da documentação da Exo e dos ensaios da Lara.
