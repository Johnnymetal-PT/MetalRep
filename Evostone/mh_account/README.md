# Módulo MH Account - Sistema de Adiantamentos

## Configuração de Adiantamentos de Clientes

Este módulo implementa um sistema robusto de adiantamentos usando reconciliação nativa do Odoo 18.

### 1. Configuração Inicial

#### 1.1 Criar Conta de Adiantamento

1. Acesse: **Contabilidade > Configuração > Plano de Contas**
2. Crie uma nova conta com as seguintes configurações:
   - **Código**: 41910001 (ou conforme seu plano de contas)
   - **Nome**: Adiantamentos de Clientes
   - **Tipo**: A Receber (asset_receivable) - **IMPORTANTE!**
   - **Reconciliável**: Sim (será marcado automaticamente)
   - **É Conta de Adiantamento**: Sim ✓
   - **Tipo de Adiantamento**: Cliente

⚠️ **IMPORTANTE**: A conta DEVE ser do tipo `asset_receivable` para permitir reconciliação com faturas.

#### 1.2 Verificar Sequências

As sequências já devem estar configuradas:
- `payment.advance.customer` - Para adiantamentos de clientes
- `payment.advance.vendor` - Para adiantamentos de fornecedores
- `payment.receipt` - Para recibos

### 2. Fluxo de Trabalho

#### 2.1 Registrar Adiantamento

1. Acesse: **Contabilidade > Clientes > Pagamentos**
2. Clique em **Criar**
3. Preencha:
   - **Tipo de Pagamento**: Recebimento
   - **Parceiro**: Selecione o cliente
   - **É Adiantamento**: Marque ✓
   - **Valor**: Valor do adiantamento
   - **Diário**: Banco ou Caixa
4. **Confirmar** o pagamento

**Lançamento Contábil Gerado:**
```
Débito:  1200003 (Banco/Caixa)         1000
Crédito: 41910001 (Adiant. Clientes)   1000
```

#### 2.2 Emitir Fatura

1. Crie a fatura normalmente
2. A fatura pode estar em **Rascunho** ou **Confirmada**

**Lançamento da Fatura:**
```
Débito:  41110001 (Contas a Receber)   1000
Crédito: 7110000 (Receita)             1000
```

#### 2.3 Aplicar Adiantamento à Fatura

**Método 1: Via Wizard (Recomendado)**

1. Na fatura, clique no botão **Aplicar Adiantamentos** (visível quando há adiantamentos)
2. Selecione os adiantamentos a aplicar
3. Clique em **Aplicar**

**Método 2: Via Reconciliação Manual**

1. Acesse: **Contabilidade > Contabilidade > Reconciliação**
2. Selecione as linhas do adiantamento e da fatura
3. Reconcilie

**Resultado da Reconciliação:**
- As linhas de 41910001 (crédito) e 41110001 (débito) são reconciliadas
- A fatura é marcada como paga (total ou parcialmente)
- O adiantamento é marcado como utilizado

### 3. Funcionalidades

#### 3.1 Reconciliação Automática
- O sistema usa reconciliação nativa do Odoo
- Suporta reconciliação parcial automática
- Mantém rastreabilidade completa

#### 3.2 Validações
- Conta de adiantamento deve ser `asset_receivable`
- Validação automática de tipos de conta
- Verificação de parceiro correspondente

#### 3.3 Rastreamento
- Campo `applied_advance_ids` na fatura mostra adiantamentos aplicados
- Campo `reconciled_invoice_ids` no pagamento mostra onde foi usado
- Mensagens no chatter documentam todas as operações

### 4. Troubleshooting

#### Erro: "Conta de adiantamento não encontrada"
**Solução**: Configure uma conta com:
- Tipo: `asset_receivable`
- Campo "É Conta de Adiantamento": Marcado
- Tipo de Adiantamento: Cliente

#### Erro: "Não foi possível encontrar a linha do adiantamento para reconciliar"
**Solução**: Verifique se:
- O adiantamento está confirmado
- O parceiro é o mesmo na fatura e no adiantamento
- A conta de adiantamento está corretamente configurada

#### Erro: "A fatura deve estar confirmada"
**Solução**: 
- O wizard confirma automaticamente faturas em rascunho
- Para reconciliação manual, confirme a fatura primeiro

### 5. Cenários de Uso

#### Cenário 1: Adiantamento Total
- Cliente paga 1000 adiantado
- Fatura de 1000 é emitida
- Aplicar adiantamento quita totalmente a fatura

#### Cenário 2: Adiantamento Parcial
- Cliente paga 600 adiantado
- Fatura de 1000 é emitida
- Aplicar adiantamento deixa 400 em aberto

#### Cenário 3: Múltiplos Adiantamentos
- Cliente tem vários adiantamentos
- Wizard permite selecionar quais aplicar
- Sistema reconcilia automaticamente

### 6. Relatórios

Os adiantamentos aparecem em:
- Extrato de Parceiros
- Aging de Contas a Receber
- Relatórios de Reconciliação
- Livros Contábeis

### 7. Segurança

- Apenas usuários com permissão de contabilidade podem aplicar adiantamentos
- Todas as operações são registradas no chatter
- Reconciliações são auditáveis

### 8. Integração

O módulo se integra com:
- Sistema de pagamentos nativo
- Reconciliação bancária
- Relatórios financeiros
- Multi-moeda (se configurado)

## Suporte

Para dúvidas ou problemas, consulte os logs em:
- `/var/log/odoo/odoo.log` - Para mensagens do sistema
- Chatter das faturas - Para histórico de operações