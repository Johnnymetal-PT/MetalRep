# Scrap com 2 Tipos — Quebra e Remediação

## Resumo

Implementação de 2 tipos de descarte no modelo `stock.scrap` do módulo `mh_picking`:

- **Quebra**: Placa destruída. Saída → conta 6842. Sobras opcionais (0 a N peças) → conta 7642.
- **Remediação**: Re-medição. Saída original → conta 6849. Novas placas obrigatórias (1 a N) → conta 7649.

Cada tipo usa uma **localização de scrap diferente**, configurada com as contas correctas:
- Localização "Quebras": valuation_out = 6842, valuation_in = 7642
- Localização "Remediações": valuation_out = 6849, valuation_in = 7649

---

## Ficheiros

### Modelos

| Ficheiro | Descrição |
|---|---|
| `stock_scrap.py` | Modelo principal — `scrap_type` (break/remediation), `scrap_line_ids`, criação de picking de entrada |
| `stock_scrap_transformation_line.py` | Modelo `stock.scrap.transformation.line` — linhas de saída (length, width, thickness, area, units_qty) |
| `stock_picking.py` | Override de `_check_duplicate_lot_groups()` para skip com `from_scrap=True` |

### Views

| Ficheiro | Descrição |
|---|---|
| `views/stock_scrap_views.xml` | Form com radio break/remediation, tabs Sobras e Novas Placas |

---

## Campos no `stock.scrap`

```
scrap_type          Selection [break, remediation]  default='break'
scrap_line_ids      One2many -> stock.scrap.transformation.line
entry_picking_id    Many2one -> stock.picking (picking de entrada gerado)
```

## Modelo `stock.scrap.transformation.line`

```
scrap_id    Many2one -> stock.scrap  (cascade)
length      Float     Comprimento
width       Float     Largura
thickness   Float     Espessura (herdada do quant, readonly)
area        Float     Computed = length x width
units_qty   Integer   Quantidade, default=1
```

---

## Fluxo

### Quebra
```
Selecionar Stock -> scrap_type = 'break'
-> (Opcional) Adicionar linhas de sobras com dimensões
-> Validar -> do_scrap() standard (saída pela conta da localização de quebras = 6842)
-> Se sobras existem: _create_scrap_entry() -> picking IN pela localização de quebras (conta 7642)
-> FIM
```

### Remediação
```
Selecionar Stock -> scrap_type = 'remediation'
-> (Obrigatório) Adicionar N linhas com novas dimensões
-> Validar -> do_scrap() standard (saída pela conta da localização de remediações = 6849)
-> _create_scrap_entry() -> picking IN pela localização de remediações (conta 7649)
-> FIM
```

---

## Contas Contabilísticas

| Conta | Tipo | Uso |
|---|---|---|
| 6842 | Gasto | Saída por quebra |
| 7642 | Rendimento | Entrada de sobra (da quebra) |
| 6849 | Gasto | Saída por remediação (placa original) |
| 7649 | Rendimento | Entrada por remediação (novas placas) |

## Configuração das Localizações

1. Criar localização "Quebras" (tipo scrap):
   - Stock Valuation Account (Outgoing) = 6842
   - Stock Valuation Account (Incoming) = 7642

2. Criar localização "Remediações" (tipo scrap):
   - Stock Valuation Account (Outgoing) = 6849
   - Stock Valuation Account (Incoming) = 7649
