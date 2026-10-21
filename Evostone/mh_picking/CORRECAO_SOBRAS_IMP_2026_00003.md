# Correcção Sobras de Quebra — IMP/2026/00003

## Contexto

Durante o import IMP/2026/00003, no dia 08/03/2026, foi feita uma quebra (SP/00021) de uma placa do **lot_group A** do artigo [141002200405] Slab Mármore (PN, Branco, Lena, 20 mm, Polido, S/N).

Dessa quebra resultaram 2 sobras que entraram em stock via **MPT/IN/00025** em novos lot_groups:
- **lot b** (id=154): 3.7698 m²
- **lot c** (id=155): 1.0001 m²

As sobras entraram ao custo provisório (3,147.12 — taxa errada 75.20) porque os custos de importação (landed costs) ainda não tinham sido aplicados.

No dia 12/03, os landed costs foram aplicados ao lot A, mas os lot_groups b e c **não receberam LC** porque entraram via MPT/IN/00025 (sobra de quebra), não via MPT/IN/00024 (picking do import).

As sobras foram vendidas no mesmo dia 12/03 (MPT/OUT/00194, S00373) ao custo provisório errado, quando o PCMP definitivo (com LC) já era 4,542.10.

---

## Correcções aplicadas

### Lot group b (id=154) — 3.7698 m²

| SVL | Operação | Antes | Depois | Contas |
|-----|----------|-------|--------|--------|
| 62991 | IN (MPT/IN/00025) | uc=3,147.12 val=11,864.01 | uc=3,122.01 val=11,769.35 | D 223 / C **7642** (era 21123) |
| 63885 | Ajuste (novo) | — | val=+5,353.46 | D 223 / C 7642 |
| 63827 | OUT (MPT/OUT/00194) | uc=3,147.12 val=-11,864.01 | uc=4,542.10 val=-17,122.81 | D 6112 / C 223 |
| | **Saldo** | **0.00** | **0.00** | |

**Account moves:**
- STJ/2026/03/0186: corrigido (21123 → 7642, valor 11,769.35)
- STJ/2026/03/0572: ajuste criado (D 223 / C 7642, valor 5,353.46)
- STJ/2026/03/0512: corrigido (valor 17,122.81)

**SOL 36709** (S00373): cost_at_confirmation 3,147.12 → 4,542.10 | pp_hist = 3,147.12

---

### Lot group c (id=155) — 1.0001 m²

| SVL | Operação | Antes | Depois | Contas |
|-----|----------|-------|--------|--------|
| 62992 | IN (MPT/IN/00025) | uc=3,147.12 val=3,147.43 | uc=3,122.01 val=3,122.32 | D 223 / C **7642** (era 21123) |
| 63886 | Ajuste (novo) | — | val=+1,420.23 | D 223 / C 7642 |
| 63828 | OUT (MPT/OUT/00194) | uc=3,147.12 val=-3,147.43 | uc=4,542.10 val=-4,542.55 | D 6112 / C 223 |
| | **Saldo** | **0.00** | **0.00** | |

**Account moves:**
- STJ/2026/03/0187: corrigido (21123 → 7642, valor 3,122.32)
- STJ/2026/03/0573: ajuste criado (D 223 / C 7642, valor 1,420.23)
- STJ/2026/03/0513: corrigido (valor 4,542.55)

**SOL 36710** (S00373): cost_at_confirmation 3,147.12 → 4,542.10 | pp_hist = 3,147.12

---

## Lógica contabilística

### Porquê 7642 (Sobras)?

As entradas via MPT/IN/00025 são **sobras de quebra**. Segundo o módulo mh_picking:
- Quebra: saída → conta 6842, entrada de sobras → conta 7642
- Remediação: saída → conta 6849, entrada → conta 7649

As entradas estavam incorrectamente na conta 21123 (Mercadorias ME Isento). Foram corrigidas para 7642 (Sobras).

### Porquê o ajuste?

As sobras entraram a 3,122.01 (custo provisório FOB). O custo real após landed costs é 4,542.10. A diferença (1,420.09/m²) foi registada como ajuste nas mesmas contas da sobra (D 223 / C 7642), porque é a complementação do custo que a quebra original deveria ter absorvido.

### PCMP = 4,542.10

```
PCMP = (1,702,031.19 + 774,194.67) / 545.1716 = 4,542.10
```

Este é o PCMP definitivo do artigo 141002200405, incluindo FOB (taxa 74.60) + todos os landed costs.
