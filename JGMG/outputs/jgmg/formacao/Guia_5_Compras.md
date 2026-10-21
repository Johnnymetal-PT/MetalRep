# Sessão 5 — Compras a fornecedores

**Cliente:** JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA · **Projeto:** Implementação Odoo · **Data:** 10/2026 · **Formadora:** Lara Cunha (Parâmetro Global)

> A interface do Odoo está em português do Brasil. Os nomes de menus e botões aparecem **a negrito, exatamente como no ecrã**.

## O que se vai ver e porquê

Depois de o cliente aceitar o orçamento, é preciso encomendar o mobiliário, os materiais e a decoração. A aplicação **Compras** regista os pedidos aos fornecedores, controla o que já chegou e liga tudo às faturas recebidas.

## O circuito, passo a passo

Menu: **Compras › Pedidos › Solicitações de cotação** → **Novo**.

1. **Fornecedor** e, se existir, **Ref. do fornecedor** (número da proposta dele).
2. Separador **Produtos** — artigos e quantidades. Se o fornecedor estiver na ficha do artigo, o preço é preenchido automaticamente.
3. **Chegada prevista**.
4. No campo **Origem**, indicar o projeto ou o pedido de venda a que a compra se destina.
5. Para pedir preço: **Enviar solicitação de cotação**. Para encomendar já: **Confirmar pedido**.
6. Quando a mercadoria chegar: **Receber** e confirmar as quantidades.
7. Quando chegar a fatura do fornecedor: registá-la (sessão 6).

## Os estados de uma compra

**SDC** (em preparação) → **SDC enviada** → **Pedido de compra** (confirmado) · ou **Cancelado**.

Na lista, duas colunas dizem o que falta:

- **Status do recebimento**: Não recebido / Recebido parcialmente / Totalmente recebido.
- **Status do faturamento**: Nada para faturar / Faturas em espera / Totalmente faturado.

## Exercício

1. Criar uma solicitação de cotação para um fornecedor, com dois artigos, e **Origem** = «Adélia Reis - Acessório Doseador».
2. **Confirmar pedido**.
3. Registar a receção parcial (só um dos artigos).
4. No fim, cancelar o pedido de teste.

## O que o Odoo passa a dar

- O que está encomendado, o que já chegou e o que falta, por fornecedor e por projeto.
- Preços dos fornecedores guardados nos artigos.
- Ligação direta entre a encomenda, a receção e a fatura do fornecedor.

## O que fica fora e o que falta decidir

- `[POR VALIDAR]` Aprovação de compras acima de um valor — se for necessária.
- Gestão de armazém avançada (localizações, rotas): fora desta fase.

## Próximos passos

1. Lançar no Odoo as próximas encomendas a fornecedores.
2. Garantir que os fornecedores habituais estão nos contactos (importação).
