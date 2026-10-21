# Numeração no Diário do Banco — Origem dos Lançamentos

## No Odoo (diário BIM)
- `account.payment` (postado) → cria **1** `account.move` no diário BIM
- `account.bank.statement.line` (reconciliada com pagamento) → pode criar **0 ou 1** move extra no diário BIM (depende do workflow 2-steps vs 3-steps)

## No Primavera/PHC
- O recibo (RC) é validado → gera **UM lançamento contabilístico** no diário "Bancos BIM"
- Importação de extracto bancário → só faz **conciliação (matching)** com RC/PG já existentes
- Se aparece uma linha do extracto sem RC/PG correspondente (ex: juros, comissões) → cria um lançamento diverso, **no mesmo diário do banco**

## Diferença chave

| | Primavera/PHC | Odoo (2-step default) | Odoo (3-step Outstanding) |
|---|---|---|---|
| Lançamento contabilístico de RC/PG | 1 (no diário do banco) | 1 (no diário do banco) | 2 (Outstanding + Banco) |
| Comissões/juros sem documento | 1 no mesmo diário | 1 no diário | 1 no diário |
| Sequência | única por diário | única por diário | única por diário (mas 2 moves do payment) |

## Conclusão

No padrão Primavera/PHC, **não há separação por origem dentro do diário** — todos os lançamentos do diário "BIM" partilham a mesma sequência (`BIM/2026/01/0001, 0002, 0003...` independente se vêm de RC, PG, comissão ou ajuste).

A separação fiscal já está garantida no nível do **documento**:
- `receipt_number = "RC/2026/0145"` → identifica que é um recibo
- O `account.move.name = BIM/2026/01/0421` é só a referência técnica do diário

## Quando "separar" faria sentido (raro)
- Se a empresa quer **visualizar facilmente** que move foi gerado por payment vs manual
- Auditoria interna específica
- → Aí activa-se "Dedicated Payment Sequence" e os moves de payments ficam com prefixo `P` (ex: `PBIM/2026/01/0001`)

## Recomendação
- **NÃO separar** — segue Primavera/PHC, mantém uma sequência por diário
- O `receipt_number` já distingue Recibos vs Pagamentos
- Mais simples, audita-se igualmente

## Ressequenciação BIM 2026 — fluxo usado

1. Buscar todos os moves do BIM 2026 ordenados por data + id
2. Para cada move, calcular o novo nome `BIM/2026/MM/00NNN` (com MM do `move.date.month` e NNN sequencial 1..832)
3. `models.execute_kw(... 'account.move', 'write', [[move_id], {'name': new_name}])` com contexto `allow_resequence_rename=True` para passar pela nossa protecção
4. Re-write para forçar recompute de `sequence_prefix`/`sequence_number` (causou o problema `made_sequence_gap` que tivemos que resolver)

Não está em ficheiro. Queres que reconstrua e guarde em `scripts/renumber_bim_2026.py` (idempotente, com dry-run) para usares de futuro em outros journals (BCI, CSH, ABSA, MOZ)?
