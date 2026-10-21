# Workflow de Numeração — Diários Bank/Cash/General/Credit

Data: 2026-05-16

## Configuração actual

- **Formato:** `PREFIX/YYYY/MM/SEQ` (ex: `BIM/2026/04/00167`)
- **Reset:** **MENSAL** (cada mês reinicia em `00001`)
- **Implementação:** Odoo standard (`_sequence_year_month_regex` → reset `year_month`)
- **Custom overrides activos:**
  - `_get_sequence_format_param` — desambigua formato `YYYY/MM` no parsing
  - `_BANK_CASH_NAME_REGEX` + `_is_year_month_seq_journal` — helpers

## Workflow operacional

### Durante o mês

- **Postas lançamentos em qualquer ordem.** O número de sequência é atribuído no momento do `Post` (não pela data).
- Cenário típico: extracto bancário do dia 24 chega depois do extracto do dia 27 — **podes postar ambos** sem bloqueio.
- O número não vai necessariamente coincidir com a ordem cronológica das datas, e **isto é fiscalmente OK** (PGC-NIRF + SAF-T MZ não exigem sequência crescente por data, apenas apresentação cronológica em relatórios).

### Antes de fechar o mês

1. **Reconciliar todas as linhas do extracto bancário** com RCs/PGs.
2. (Opcional) **Resequenciar** para alinhar sequência com data:
   - `Acções → Resequenciar` (modo developer, restrito a admin do sistema)
   - O wizard reordena os números dentro do mês pela data de cada lançamento
   - Resultado: `BIM/2026/04/00001` = lançamento mais antigo de Abril, ..., `BIM/2026/04/00167` = mais recente

### Fecho do mês

- **Settings → Accounting → Lock Dates → Fiscal Year Lock Date**
- Definir = último dia do mês (ex: `2026-04-30`)
- A partir deste ponto:
  - Nenhum lançamento pode ser criado ou alterado com `date ≤ lock_date`
  - O Odoo bloqueia tentativas automaticamente

## Protecções activas (custom mh_account)

### Imutabilidade após numeração (write)

Para `bank/cash/general/credit`, após numeração (`name != '/'`), bloqueia alteração de:
- `name` (número do lançamento)
- `date`
- `journal_id`
- `company_id`

Bypass: context `allow_resequence_rename=True` (usado internamente pelo wizard de resequenciar).

### Eliminação de lançamentos

O `mh_base` não acrescenta restrições fiscais de Moçambique à eliminação de
lançamentos. Aplicam-se as validações standard do Odoo para documentos em
rascunho ou anulados.

### Validação data vencimento (action_post)

- `invoice_date_due ≥ invoice_date` em facturas

### Chronology check **desactivado** (comentado)

O bloco "Cronologia dentro do mês" está comentado em `action_post`. Estava a impedir backdating dentro do mesmo mês, o que conflitua com o cenário real de extractos bancários atrasados.

Para reactivar, descomentar em `account_move.py` → `action_post()`.

## Wizard de Resequenciar

- Localizado em `account.resequence.wizard` (Odoo standard)
- Estendido em `mh_account/models/account_resequence_wizard.py`:
  - Adiciona context `allow_resequence_rename=True` para passar pela protecção `write()`
  - **Restrito a `base.group_system`** — apenas administradores do sistema
- Acede via: modo developer → Acções → Resequenciar

## Componentes técnicos

| Ficheiro | Função |
|---|---|
| `mh_account/models/account_move.py` | Overrides de numeração + protecções + `action_post` |
| `mh_account/models/account_resequence_wizard.py` | Bypass de protecção + restrição admin no wizard |
| `mh_base/models/delete_protection.py` | Proibição de unlink em moves numerados |

## Histórico

- **Versão anterior (até 2026-05-15):** reset **anual** com chronology check global no diário
- **Versão actual (2026-05-16):** reset **mensal** com chronology check desactivada
- Migração: corrida resequenciação BIM 2026 via wizard (5 meses, 837 entries)
- Backup do ficheiro: `account_move.py.bak.2026-05-15_anual`

## Referências legais

- **Lei nº 7/2014 (IVA MZ)** — Art. 27/28: numeração sequencial
- **PGC-NIRF MZ** — Princípio de apresentação cronológica do diário
- **SAF-T MZ** (vigor 2026) — `TransactionID` único, ordem cronológica no export
- **Odoo standard** — `account.move._sequence_year_month_regex` para reset mensal
