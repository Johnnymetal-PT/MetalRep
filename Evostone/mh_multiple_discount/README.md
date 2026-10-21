# MH Multiple Discount

## Descrição

Módulo que adiciona suporte a **4 descontos** em linhas de pedidos de venda e faturas, com dois modos de cálculo:

- **Multiplicativo** (padrão): Descontos aplicados sequencialmente
- **Aditivo**: Descontos somados antes de aplicar

## Características

### Campos Adicionados

**Em `sale.order.line` e `account.move.line`:**

- `discount` (Float) - Desconto 1% (campo padrão do Odoo)
- `discount2` (Float) - Desconto 2%
- `discount3` (Float) - Desconto 3%
- `discount4` (Float) - **Desconto 4% (NOVO)**
- `discounting_type` (Selection) - Tipo de cálculo: "Additive" ou "Multiplicative"

### Modos de Cálculo

#### Multiplicativo (Padrão)
Descontos são aplicados em sequência sobre o valor já descontado:

**Exemplo:** Preço R$ 100,00 com descontos 30%, 20%, 10%, 5%
```
100,00 → 70,00 → 56,00 → 50,40 → 47,88
Desconto total efetivo: 52,12%
```

#### Aditivo
Todos os descontos são somados primeiro (máximo 100%):

**Exemplo:** Preço R$ 100,00 com descontos 30%, 20%, 10%, 5%
```
30% + 20% + 10% + 5% = 65%
100,00 × (1 - 0,65) = 35,00
```

## Transferência de Dados

Quando um pedido de venda é convertido em fatura, **TODOS** os campos são transferidos automaticamente:

- ✅ discount
- ✅ discount2
- ✅ discount3
- ✅ discount4
- ✅ discounting_type

**Garantia:** O valor calculado no pedido será exatamente o mesmo na fatura!

## Estrutura Unificada

Diferente dos módulos OCA (`sale_triple_discount` e `account_invoice_triple_discount`), este módulo mantém a **MESMA estrutura de campos** em vendas e faturas:

- Usa `discount` (campo padrão) em vez de `discount1`
- Mesmos métodos em ambos os modelos
- Cálculos idênticos

## Instalação

### Instalação Automática (Recomendado)

Este módulo é instalado **automaticamente** quando você instala o módulo `mh_sale`:

1. Vá em Apps → Procure por "MH Vendas" (mh_sale)
2. Clique em "Instalar"
3. O `mh_multiple_discount` será instalado automaticamente junto! ✅

### Instalação Manual

1. Copie o módulo para a pasta `addons`
2. Atualize a lista de aplicativos
3. Instale "MH Multiple Discount"

## Dependências

- `mh_sale` (módulo principal de vendas MH)
- `sale_management`
- `account`

## Permissões

Todos os campos de desconto são visíveis apenas para usuários com a permissão:
- **Grupo:** `product.group_discount_per_so_line` (Discount per Sales Order Line)

## Uso

### No Pedido de Venda:
1. Crie um pedido de venda
2. Adicione produtos
3. Preencha os campos de desconto (discount, discount2, discount3, discount4)
4. Escolha o tipo de cálculo (Multiplicativo ou Aditivo)
5. O preço será calculado automaticamente

### Na Fatura:
1. Crie a fatura a partir do pedido de venda (ou manualmente)
2. Todos os descontos serão transferidos automaticamente
3. O cálculo será feito com o mesmo tipo escolhido no pedido

## Testes

O módulo inclui testes unitários completos:

```bash
odoo-bin -c odoo.conf --test-enable -u mh_multiple_discount --stop-after-init
```

## Casos de Uso

### 1. Cliente Atacadista com Promoção
- Desconto 1: 30% (Cliente atacadista)
- Desconto 2: 20% (Promoção sazonal)
- Desconto 3: 10% (Pagamento à vista)
- Desconto 4: 5% (Volume)
- Tipo: Multiplicativo
- Resultado: 52,12% de desconto total

### 2. Promoção Acumulativa
- Desconto 1: 20% (Cupom 1)
- Desconto 2: 15% (Cupom 2)
- Desconto 3: 10% (Cupom 3)
- Desconto 4: 5% (Cashback)
- Tipo: Aditivo
- Resultado: 50% de desconto total

## Autor

**MH**

## Licença

AGPL-3.0 or later

## Versão

18.0.1.0.0
