# mh_import_adjustment — Próximos Passos

Data: 2026-05-13

End-to-end validado em Stone Trading (DB `stone-trading-mhc-main-090126`):
- Hook detector cria ADJ draft ao postar factura com linhas órfãs (`landed_cost_ok=True` sem `purchase_line_id`)
- `action_apply` cria 2º Landed Cost + Ajuste CMV + SVL
- Caso teste validado: `IMP/2026/00010` → `ADJ/2026/0003` aplicado correctamente (contas balanceadas, SVL ajustado, PCMP actualizado)

Casos validados: `IMP/2026/00009` (ADJ/2026/0002) e `IMP/2026/00010` (ADJ/2026/0003).

---

## 1. Testar caso multi-produto

Cenário: 1 IMP com **mais que 1 produto físico** (não só 1).

Verificar:
- LC distribui o ajuste pelos vários produtos (split por valor — `by_current_cost_price`).
- Ajuste CMV gera **N pares D/C** (um por produto com qty vendida).
- Cria **N SVLs** (um por produto) — todos a apontar para o mesmo `account_move_id`.
- Account move final balanceado (cada par D output / C stock_valuation por produto).

Stress test: produtos com **categorias diferentes** (logo, contas `stock_output` e `stock_valuation` diferentes) — confirmar que o move tem várias contas distintas.

---

## 2. Edge cases

| Caso | Comportamento esperado |
|---|---|
| Factura sem POs linkadas (nenhuma linha tem `purchase_line_id`) | Hook não consegue identificar IMP → loga warning, **não cria ADJ** |
| Várias linhas Acerto com produtos diferentes | Uma única ADJ com `source_invoice_line_ids` múltiplos, somatório em `amount` |
| Factura linkada a 2 IMPs (POs em IMPs distintos) | Hook escolhe primeiro IMP e regista warning. Considerar UX explícita |
| Qty vendida = qty IMP (todo o lote já vendido) | LC distribui sobre 10, mas 10/10 vendidos → CMV cobre os 5.000 inteiros. SVL = -5.000 |
| Qty vendida > qty IMP (impossível pelo `_get_qty_sold_since` desde IMP done, mas validar) | Validar que o domínio do SVL só apanha out posteriores |
| Acerto NEGATIVO (factura veio abaixo da PO — refund) | `amount` negativo no ADJ; LC com cost line negativa? Validar comportamento do `stock.landed.cost` |
| Postar factura com linha Acerto mas IMP ainda em `partial` | Hook cria ADJ mas IMP não é `done` ainda — esperar finalização ou bloquear apply até IMP=done |
| ADJ já aplicado, depois reverter LC manualmente | Sem mecanismo automático de reversão do ADJ — fica state='applied' órfão |

**Action items dos edge cases:**
- Adicionar validação em `action_apply` que IMP esteja em state='done'.
- Implementar `action_cancel` real para state='applied' (reverter LC e CMV move via Odoo standard `_reverse_moves`).
- Considerar UX para ambiguidade multi-IMP (wizard escolher manualmente).

---

## 3. Outros itens da lista de pendentes

Pendentes operacionais que ficaram fora do escopo deste módulo:

- **Casas decimais — Stone**: ajustar `decimal.precision` em algum sítio específico
- Outros que possam surgir

---

## Limpeza / Reforço futuro

- [ ] Adicionar wizard "Criar Ajuste manualmente" no IMP (botão para casos onde o hook não detectou)
- [ ] Mostrar ADJ relacionado na vista da factura (smart button — já tem)
- [ ] Botão "Reverter" no ADJ aplicado (cria reversão automática de LC + CMV + SVL)
- [ ] Testes unitários
- [ ] Documentação técnica em `docs/fluxo.md` (diagrama mermaid)
- [ ] Tradução PT (i18n)
