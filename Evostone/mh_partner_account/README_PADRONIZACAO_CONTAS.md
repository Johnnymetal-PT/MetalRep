# Padronização de Contas de Parceiros — Stone Trading

## Data: 30/03/2026

---

## Lógica de Numeração

### Formato do código da conta
```
PREFIXO + nr_cliente/nr_fornecedor (5 dígitos)
```

### Clientes
| Tipo | Prefixo | Exemplo (nr=1) |
|------|---------|----------------|
| Nacional (Moçambique) | 4111 | 411100001 |
| Estrangeiro | 4112 | 411200001 |

### Fornecedores
| Tipo | Prefixo | Exemplo (nr=1) |
|------|---------|----------------|
| Nacional (Moçambique) | 4211 | 421100001 |
| Estrangeiro | 4212 | 421200001 |

### Regra
- O `nr_cliente`/`nr_fornecedor` é **global** (sequência única independente do prefixo)
- O mesmo número aparece nos últimos dígitos da conta, independente de ser nacional ou estrangeiro
- Ex: fornecedor nr=10 nacional → 421100010, fornecedor nr=10 estrangeiro → 421200010

---

## Configuração (res.company.partner.account.config)

| Parâmetro | Clientes | Fornecedores |
|-----------|----------|--------------|
| prefix | 411 | 421 |
| sequence_digits | 5 | 5 |
| national_prefix | 4111 | 4211 |
| foreign_prefix | 4112 | 4212 |
| distinguish_nationality | True | True |

---

## Campos Adicionados

### account.account
- **`is_orphan`** (Boolean, default=False): Marca contas importadas do sistema antigo sem parceiro associado. Excluídas da sequência automática.

### res.partner
- **`skip_account_creation`** (Boolean, default=False): Quando marcado, não cria conta individual (4111/4211) nem atribui nr_cliente/nr_fornecedor. Usado para funcionários, parceiros internos ou casos especiais.

---

## Contas Órfãs

Contas migradas do sistema antigo que não têm parceiro associado. Renumeradas para os últimos números para não conflitar com a sequência automática.

### Clientes
- **4111**: 411199999 descendo (67 contas)
- **4112**: 411299999 descendo (2 contas)

### Fornecedores
- **4211**: 421199999 descendo (26 contas)
- **4212**: 421299999 descendo (5 contas)

Todas marcadas com `is_orphan=True`.

---

## Parceiros com skip_account_creation

### Clientes
| Parceiro | Conta actual | Motivo |
|----------|-------------|--------|
| 99. Rui Guilherme Pinto Rodrigues | 45910001 | Funcionário (conta 459) |

### Fornecedores
| Parceiro | Conta actual | Motivo |
|----------|-------------|--------|
| 99. Rui Guilherme Pinto Rodrigues | 46710001 | Funcionário (conta 467) |
| Olga Almeida - Funcionaria | 4622 | Funcionária (remunerações) |
| Emidio Romeu Guambe | 4622 | Funcionário (remunerações) |
| Aide Dinis Mufapa - Trabalhador | 4622 | Funcionário (remunerações) |
| José Luís Chau | 4622 | Funcionário (remunerações) |
| Chaide José Chico Chaua | 4622 | Funcionário (remunerações) |

---

## Contas Partilhadas (PEMARO / Mário Mechião)

O PEMARO e o Mário partilhavam a mesma conta (migração antiga). Resolução:

### Clientes
- PEMARO (nr=1): **411100001** (conta com movimentos, mantida)
- Mário (nr=50): **411100050** (conta nova criada)

### Fornecedores
- PEMARO (nr=1): **421100001** (conta nova criada)
- Mário (nr=78): **421100078** (conta nova criada)

Os movimentos antigos ficam na conta original. Futuras transacções vão para as contas novas.

---

## Alterações no Código

### models/account_account.py (NOVO)
- Campo `is_orphan` no `account.account`

### models/res_partner.py
- Campo `skip_account_creation`
- `_create_partner_account()`: verifica `skip_account_creation` antes de criar
- `ensure_partner_account()`: verifica `skip_account_creation`
- `_get_next_sequence_from_accounts()`: filtra `is_orphan=False`
- Usa `nr_cliente/nr_fornecedor` como dígitos da conta (em vez de sequência por prefixo)

### views/res_partner_views.xml
- Campo `skip_account_creation` visível no tab Contabilidade

---

## Resultado Final

### Clientes
| | Valor |
|---|---|
| Total parceiros | 166 |
| Contas correctas | 166/166 ✅ |
| Sequência | 1-166 sem buracos ✅ |

### Fornecedores
| | Valor |
|---|---|
| Total parceiros | 165 |
| Contas correctas | 165/165 ✅ |
| Sequência | 1-165 sem buracos ✅ |

---

## Backups

- `BACKUP_CLIENTES_RENUMERACAO.csv` — nr_cliente, conta antiga, saldo, conta nova
- `BACKUP_FORNECEDORES_RENUMERACAO.csv` — nr_fornecedor, conta antiga, saldo, conta nova

---

## Código RPC usado

### Marcar órfãs
```python
# Buscar contas sem parceiro
orfas = [c for c in contas if c['id'] not in active_acc_ids]
# Marcar is_orphan + renumerar
models.execute_kw(db, uid, pw, 'account.account', 'write', [orfa_ids, {'is_orphan': True}])
for i, c in enumerate(orfas):
    new_code = '42119%s' % str(9999 - i)
    models.execute_kw(db, uid, pw, 'account.account', 'write', [[c['id']], {'code': new_code}])
```

### Renumerar contas activas
```python
for p in partners:
    nr = p['nr_fornecedor']
    prefix = '4212' if estrangeiro else '4211'
    new_code = '%s0%s' % (prefix, str(nr).zfill(4))
    # Renumerar ou criar conta
    models.execute_kw(db, uid, pw, 'account.account', 'write', [[acc_id], {'code': new_code}])
```

### Marcar especiais (funcionários)
```python
models.execute_kw(db, uid, pw, 'res.partner', 'write', [[partner_id], {
    'skip_account_creation': True,
    'nr_cliente': 0,  # ou nr_fornecedor
}])
```

### Fechar buracos na sequência
```python
for gap in missing:
    partners_above = search([('nr_fornecedor', '>', gap)])
    for p in partners_above:
        write(p.id, {'nr_fornecedor': p.nr_fornecedor - 1})
```
