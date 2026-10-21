# Sessão 3 — Orçamentos e Vendas

**Cliente:** JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA · **Projeto:** Implementação Odoo · **Data:** 10/2026 · **Formadora:** Lara Cunha (Parâmetro Global)

> A interface do Odoo está em português do Brasil. Os nomes de menus e botões aparecem **a negrito, exatamente como no ecrã**.

## O que se vai ver e porquê

O orçamento é a proposta ao cliente: design, mobiliário, materiais e montagem. Quando o cliente aceita, é confirmado e passa a pedido de venda — e é a partir dele que nascem o projeto, as compras e a fatura. Fazer o orçamento no Odoo evita voltar a escrever a mesma informação noutros sítios.

## O circuito, passo a passo

Menu: **Vendas › Pedidos › Cotações** → **Novo** (ou, a partir de uma oportunidade, **Nova cotação**).

1. **Cliente** — escolher ou criar (completar NIF e morada).
2. **Expiração** — até quando a proposta é válida.
3. **Condições de pagamento** — ex.: «Pagamento imediato», «30 dias», «30% agora, restante em 60 dias».
4. Separador **Linhas do pedido**:
   - **+ Adicionar seção** — organizar por divisões ou fases: «Sala», «Cozinha», «Montagem».
   - **Adicionar linha** — escolher o artigo, a quantidade e confirmar o preço.
   - **Adicionar nota** — observações, condições, prazos.
5. Conferir o IVA de cada linha e o total.
6. **Visualizar** — ver o documento como o cliente o recebe. **Baixar** gera o PDF.
7. **Enviar** — envia por email. O estado passa a **Cotação enviada**.
8. Cliente aceitou → **Confirmar**. O documento passa a **Pedido de venda**.

## O que acontece ao confirmar

- Se o orçamento tiver a linha **«Projeto de design de interiores»**, o **projeto é criado automaticamente**, ligado ao cliente e já com as fases da empresa (Ficha cliente → … → Auditoria) — sem o criar à mão. O nome do projeto pode ser ajustado depois.
- As mercadorias geram a entrega ao cliente.
- O pedido fica pronto a faturar (**Criar fatura**) — sessão 6.

## Os estados de um orçamento

**Cotação** (em preparação) → **Cotação enviada** → **Pedido de venda** (aceite) · ou **Cancelado**.

## Exercício

1. Criar um orçamento para a Adélia Reis com três secções («Peça», «Acessórios», «Montagem») e pelo menos uma linha em cada.
2. **Visualizar** o resultado.
3. Confirmar um orçamento **de teste** e ver o projeto criado. No fim, cancelar o orçamento de teste.

## O que o Odoo passa a dar

- Propostas com aspeto profissional, iguais para toda a equipa.
- Lista de orçamentos por estado: o que está enviado e sem resposta salta à vista.
- **Relatórios** de vendas por período, vendedor, artigo e cliente.

## O que fica fora e o que falta decidir

- `[POR VALIDAR]` Modelo de orçamento com texto fixo (condições gerais, prazos) — a definir.
- A emissão da fatura ao cliente é tratada na sessão 6.

## Próximos passos

1. Fazer os próximos orçamentos no Odoo, a partir do CRM.
2. Enviar à Parâmetro Global um orçamento-tipo atual, para alinhar o aspeto e as condições.
