# MH Sale Pricelist Lot - Exemplos de Uso

## 📋 Guia Rápido de Configuração

### Passo 1: Instalar o Módulo

1. Ir para `Aplicações`
2. Procurar por "MH Sale Pricelist Lot Integration"
3. Clicar em `Instalar`

### Passo 2: Verificar Dependências

Certifique-se que os seguintes módulos estão instalados:
- ✅ mh_base
- ✅ mh_inventory
- ✅ mh_picking (para base.lot.group e lot.price.group)
- ✅ mh_sale (para lot_id em sale.order.line)

---

## 🎯 Casos de Uso Práticos

### Caso 1: Desconto VIP em Mármores Carrara

**Objetivo:** Clientes VIP recebem 10% de desconto em todos os lotes de Carrara

**Configuração:**

```
Vendas → Configuração → Listas de Preços
1. Criar/Editar: "Clientes VIP"
2. Adicionar linha:
   - Aplicar em: Base Lot Group
   - Base Lot Group: CARRARA_WHITE
   - Cálculo: Percentual (desconto)
   - Percentual: 10%
```

**Resultado:**
- Cliente VIP seleciona qualquer lote CARRARA_WHITE
- Preço automaticamente reduzido em 10%
- Sem necessidade de alterar preço dos lotes individuais

---

### Caso 2: Preço Premium para Lajes Grandes

**Objetivo:** Lajes com dimensões 3.00 x 1.50 têm preço 20% maior

**Configuração:**

```
Vendas → Configuração → Listas de Preços
1. Editar lista de preços padrão
2. Adicionar linha:
   - Aplicar em: Lot Price Group
   - Lot Price Group: CARRARA_WHITE-3.00x1.50
   - Cálculo: Percentual (markup)
   - Percentual: 20%
```

**Resultado:**
- Apenas lotes com dimensões exatas 3.00 x 1.50 ficam 20% mais caros
- Outras dimensões mantêm preço normal

---

### Caso 3: Desconto por Volume

**Objetivo:** Compras de 10+ lotes da mesma base group → 5% desconto

**Configuração:**

```
Vendas → Configuração → Listas de Preços
1. Adicionar linha:
   - Aplicar em: Base Lot Group
   - Base Lot Group: CARRARA_WHITE
   - Qtd Mínima: 10
   - Cálculo: Percentual (desconto)
   - Percentual: 5%
```

**Resultado:**
- Vendendo 1-9 lotes: preço normal
- Vendendo 10+: desconto de 5% aplicado automaticamente

---

### Caso 4: Promoção de Black Friday

**Objetivo:** 15% desconto em TODOS os mármores durante 1 semana

**Configuração:**

```
Vendas → Configuração → Listas de Preços
1. Criar: "Black Friday 2024"
2. Adicionar múltiplas linhas (uma por base group):

Linha 1:
   - Aplicar em: Base Lot Group
   - Base Lot Group: CARRARA_WHITE
   - Data Início: 2024-11-24
   - Data Fim: 2024-11-30
   - Cálculo: Percentual (desconto)
   - Percentual: 15%

Linha 2:
   - Aplicar em: Base Lot Group
   - Base Lot Group: STATUARIO
   - Data Início: 2024-11-24
   - Data Fim: 2024-11-30
   - Cálculo: Percentual (desconto)
   - Percentual: 15%

... (repetir para cada base group)
```

**Resultado:**
- Durante a Black Friday: todos os lotes ficam 15% mais baratos
- Após 30/11: volta automaticamente ao preço normal

---

### Caso 5: Preço Fixo para Lote Específico com Defeito

**Objetivo:** Lote com defeito leve → vender por €500 fixo

**Configuração:**

```
Opção A - Usando Pricelist:
1. Criar lot.price.group para esse lote específico
2. Adicionar regra:
   - Aplicar em: Lot Price Group
   - Lot Price Group: [selecionar o grupo do lote com defeito]
   - Cálculo: Preço fixo
   - Preço: 500.00

Opção B - Usando Preço Direto (mais simples):
1. Ir ao lote individual (stock.lot)
2. Definir "Preço de Venda" = 500.00
3. Sistema usa fallback (mais rápido)
```

**Resultado:**
- Lote sempre vendido por €500
- Outros lotes do mesmo grupo mantêm preço normal

---

### Caso 6: Preço Diferente por País

**Objetivo:** Clientes de Angola pagam 10% a mais (devido a custos logísticos)

**Configuração:**

```
Vendas → Configuração → Listas de Preços
1. Criar: "Angola"
2. Configurar:
   - País: Angola
   - Moeda: AOA (ou EUR)

3. Adicionar linha:
   - Aplicar em: Base Lot Group
   - Base Lot Group: CARRARA_WHITE (ou Global para todos)
   - Cálculo: Percentual (markup)
   - Percentual: 10%
```

**Resultado:**
- Cotações para Angola: preço automaticamente 10% maior
- Clientes locais: preço normal

---

### Caso 7: Combinação Complexa

**Objetivo:** Cliente VIP + compra volume + laje grande = múltiplos descontos

**Configuração:**

```
Lista "VIP":
Regra 1 (Base):
   - Base Lot Group: CARRARA_WHITE
   - Cálculo: -10% (desconto VIP)

Regra 2 (Volume):
   - Base Lot Group: CARRARA_WHITE
   - Qtd Mín: 10
   - Cálculo: -5% adicional

Regra 3 (Premium por tamanho):
   - Lot Price Group: CARRARA_WHITE-3.00x1.50
   - Cálculo: +20% (tamanho premium)
```

**Prioridade de Aplicação:**
1. Sistema escolhe regra MAIS ESPECÍFICA que aplica
2. Lot Price Group (regra 3) tem prioridade sobre Base Lot Group (regras 1 e 2)
3. Entre regras do mesmo tipo, quantidade maior tem prioridade

**Resultado:**
- Laje 3.00x1.50: aplica regra 3 (+20%)
- Laje 2.00x1.00 com 10+ unidades: aplica regra 2 (-5%)
- Laje 2.00x1.00 com 1-9 unidades: aplica regra 1 (-10%)

---

## 🔧 Testando o Sistema

### Teste Básico

1. **Criar um Base Lot Group** (se não existe)
   ```
   Picking → Configuração → Base Lot Groups
   - Nome: TEST_MARBLE
   - Produto: [selecionar produto]
   ```

2. **Criar Lot Price Group** (se não existe)
   ```
   Picking → Configuração → Lot Price Groups
   - Base Lot Group: TEST_MARBLE
   - Comprimento: 2.00
   - Largura: 1.00
   ```

3. **Criar Lote**
   ```
   Inventário → Produtos → Lotes/Números de Série
   - Produto: [mesmo produto]
   - Nome: TEST_MARBLE-001
   - Grupo de Preço: [selecionar o price group criado]
   - Preço de Venda: 100.00 (fallback)
   ```

4. **Criar Regra de Pricelist**
   ```
   Vendas → Configuração → Listas de Preços → [Editar]
   - Aplicar em: Base Lot Group
   - Base Lot Group: TEST_MARBLE
   - Cálculo: Percentual (desconto)
   - Percentual: 20%
   ```

5. **Criar Cotação de Teste**
   ```
   Vendas → Cotações → Criar
   - Cliente: [qualquer]
   - Lista de Preços: [a que criou regra]
   - Adicionar linha:
     * Produto: [o produto do teste]
     * Lote: TEST_MARBLE-001
   ```

6. **Verificar Resultado**
   ```
   Preço esperado: 100.00 - 20% = 80.00
   Se aparecer 80.00 → ✅ FUNCIONOU!
   Se aparecer 100.00 → ⚠️ Verificar configuração
   ```

---

## 🐛 Troubleshooting

### ❌ Preço não mudou ao selecionar lote

**Possíveis causas:**

1. **Lote não tem price_group_id**
   - Verificar: Abrir lote → campo "Grupo de Preço" deve estar preenchido
   - Solução: Atribuir lote a um price group

2. **Regra de pricelist não aplica**
   - Verificar: Base Lot Group da regra corresponde ao do lote?
   - Verificar: Data atual está dentro do range (se configurado)?
   - Verificar: Quantidade atende min_quantity?

3. **Lista de preços errada**
   - Verificar: Sale Order está usando a lista de preços correta?
   - Solução: Mudar lista no cabeçalho da cotação

4. **Regra com prioridade menor**
   - Verificar: Existe outra regra mais específica?
   - Solução: Ajustar `applied_on` ou sequência

### ❌ Erro ao salvar regra de pricelist

**Erro:** "Please specify a base lot group for this pricelist rule"

**Causa:** Campo obrigatório não preenchido

**Solução:**
1. Se "Aplicar em" = "Base Lot Group" → preencher "Base Lot Group"
2. Se "Aplicar em" = "Lot Price Group" → preencher "Lot Price Group"

### ❌ Múltiplas regras conflitantes

**Situação:** Duas regras aplicam ao mesmo lote

**Como o sistema decide:**

Ordem de prioridade (do mais específico para mais genérico):
```
1. Lot Price Group (dimensões exatas)
2. Base Lot Group (nome base)
3. Product Variant
4. Product
5. Category
6. Global
```

Dentro do mesmo nível:
- Quantidade maior tem prioridade
- ID mais recente tem prioridade

**Solução:**
- Ajustar especificidade das regras
- Usar datas para separar regras temporais
- Usar qtd mínima para separar regras de volume

---

## 📊 Comparação: Antes vs Depois

### ANTES (sem módulo)

**Para dar desconto em lotes Carrara:**
```
1. Ir em cada lote individual
2. Calcular preço com desconto manualmente
3. Alterar "Preço de Venda" do lote
4. Repetir para TODOS os lotes (50+ lotes!)
5. Lembrar de reverter depois da promoção
6. Calcular desconto por volume manualmente
```
⏱️ **Tempo:** 30+ minutos
😓 **Erro prone:** Alto
🔄 **Manutenção:** Difícil

### DEPOIS (com módulo)

**Para dar desconto em lotes Carrara:**
```
1. Criar regra de pricelist
2. Aplicar em: Base Lot Group
3. Selecionar: CARRARA_WHITE
4. Desconto: 10%
5. Salvar
```
⏱️ **Tempo:** 30 segundos
✅ **Automatizado:** Aplica a TODOS os lotes
🔄 **Manutenção:** Fácil (liga/desliga regra)
📅 **Temporal:** Suporta datas de início/fim

---

## 💡 Dicas Avançadas

### Dica 1: Estruturar Pricelists por Tipo de Cliente

```
Lista "Revendedores":
- Todas as base groups: -15%
- Min qty 50: -20%

Lista "Construtoras":
- Todas as base groups: -10%
- Min qty 100: -15%

Lista "Clientes Finais":
- Sem descontos (preço direto do lote)
```

### Dica 2: Usar Datas para Promoções Automáticas

```
Regra "Verão":
- Data início: 01/06
- Data fim: 31/08
- Desconto: -10%

Regra "Natal":
- Data início: 01/12
- Data fim: 31/12
- Desconto: -15%
```

Sistema ativa/desativa automaticamente!

### Dica 3: Combinar com Preço Direto

```
Estratégia híbrida:
- Lotes normais: usar pricelist (flexível)
- Lotes com defeito: preço direto no lote (override)
- Lotes de promoção: pricelist com datas

O sistema escolhe automaticamente a melhor opção!
```

---

## 📞 Suporte

Se tiver dúvidas:
1. Consultar README.md (documentação técnica)
2. Verificar logs do Odoo (modo debug)
3. Contactar Make It Happen, SA

---

**Autor:** Make It Happen, SA
**Versão:** 18.0.1.0.0
**Data:** Janeiro 2025
