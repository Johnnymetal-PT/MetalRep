# Compras e custos de destino — fluxo standard Odoo 18

## Compra sem custos adicionais

1. Abrir **Compras > Pedidos > Pedidos de Cotação** e criar o pedido.
2. Confirmar fornecedor, posição fiscal, artigos, quantidades, preços e impostos.
3. Clicar em **Confirmar Pedido**. O pedido é confirmado diretamente, sem escolher um tipo de receção.
4. Abrir o botão inteligente **Receções**.
5. Registar as quantidades e os lotes ou números de série aplicáveis.
6. Clicar em **Validar**.

## Compra com frete, seguro, direitos ou outros custos

1. Confirmar e receber a mercadoria pelo mesmo fluxo anterior.
2. Registar a fatura em **Contabilidade > Fornecedores > Faturas**. Se o custo vier na fatura da mercadoria, usar essa mesma fatura; se vier do transitário, seguradora ou despachante, criar uma fatura separada desse fornecedor.
3. Na linha da fatura, usar um produto de serviço com **É um custo de destino** ativo.
4. Confirmar a fatura e clicar em **Criar custos de destino**.
5. No custo de destino, selecionar a receção da mercadoria.
6. Confirmar o método de divisão: igual, quantidade, custo atual, peso ou volume.
7. Clicar em **Calcular** e conferir a distribuição na aba de ajustes de valorização.
8. Clicar em **Validar** apenas depois da conferência.

O botão **Criar custos de destino** cria a ligação entre a fatura e o custo de destino. A seleção em **Transferências** liga depois esse custo à receção da mercadoria. O botão inteligente **Custos de destino** da fatura permite consultar essa associação.

Também é possível criar o registo em **Inventário > Operações > Custos de destino**, mas o fluxo iniciado na fatura é preferível porque mantém a associação contabilística automática.

## Regras importantes

- O método de custeio usado é **Custo Médio (AVCO)** standard do Odoo.
- A posição fiscal do fornecedor continua a distinguir compras nacionais, UE e extra-UE.
- O antigo menu **Importações** deixa de ser usado; os registos existentes ficam disponíveis apenas como histórico técnico.
- Não ativar **Valorização por lote/número de série** em artigos com movimentos existentes sem validação prévia da equipa de suporte.
- Antes de validar um custo de destino, confirmar sempre a receção, os produtos de custo, os valores e o método de divisão.

## O que enviar ao suporte em caso de dúvida

- Número do pedido de compra.
- Número da receção.
- Fatura do custo adicional.
- Método de divisão pretendido.
- Indicação de compra nacional, UE ou extra-UE.

## Cenário A-Z de validação

O guião `guioes/evo_prova_landed_cost_a_z.py` cria quatro artigos temporários e executa o processo completo numa transação revertida:

| Registo | Quantidade | Preço/custo | Método de divisão |
|---|---:|---:|---|
| Artigo A | 10 | 100,00 | — |
| Artigo B | 5 | 200,00 | — |
| Frete | 1 | 300,00 | Quantidade |
| Seguro | 1 | 100,00 | Custo atual |

Os dois artigos começam com valor total de 1 000,00 cada. O frete atribui 200,00 ao artigo A e 100,00 ao artigo B; o seguro atribui 50,00 a cada artigo. O resultado esperado é:

- Artigo A: custo adicional 250,00 e custo médio final 125,00.
- Artigo B: custo adicional 150,00 e custo médio final 230,00.
- Valorização total: 2 400,00, integralmente ligada à fatura de custos de 400,00.

### Validação manual na staging

O guião `guioes/evo_preparar_validacao_landed_cost.py` deixa preparados os seguintes rascunhos:

- Pedido de compra identificado pela referência de fornecedor `VALIDACAO-LC-20260916`.
- Fatura de fornecedor em rascunho com a referência `VALIDACAO-LC-20260916`.
- Artigos `VALIDACAO-LC-20260916-A` e `VALIDACAO-LC-20260916-B`.
- Serviços `VALIDACAO-LC-20260916-FRETE` e `VALIDACAO-LC-20260916-SEGURO`.

Para validar pela interface:

1. Abrir o pedido pela referência, confirmar e validar a receção integral.
2. Confirmar que os custos médios dos artigos A e B ficam em 100,00 e 200,00.
3. Abrir a fatura pela referência, publicar e clicar em **Criar custos de destino**.
4. Selecionar a receção criada no passo 1 e clicar em **Calcular**.
5. Confirmar ajustes de 250,00 para o artigo A e 150,00 para o artigo B.
6. Validar o custo de destino e confirmar custos médios finais de 125,00 e 230,00.
7. Na fatura, usar o botão inteligente **Custos de destino** para regressar à associação.
