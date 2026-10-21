# Tutorial — Confirming a fornecedores (HMD)

> ⚠️ **RASCUNHO INTERNO — processo a padronizar antes de virar tutorial de cliente.**
> Confirming **não tem módulo**: é contabilidade standard com uma **conta de dívida
> dedicada**. O fluxo abaixo foi **observado na BD de produção HMD** (mar–mai 2026),
> mas ainda é recente e inconsistente — confirmar o procedimento oficial antes de
> publicar/gravar vídeo.

## O que é

No **confirming** (reverse factoring), o banco paga os fornecedores e a HMD paga ao
banco mais tarde. A dívida ao banco fica registada numa **conta de passivo de
confirming**.

## Estrutura existente na HMD (observada na BD)

| Elemento | Valor real |
|---|---|
| Conta de dívida (passivo) | **`2789 CONFIRMING`** (passivo corrente) ← onde vive a dívida |
| Conta tesouraria | `124 CONFIRMING` (ativo; praticamente sem uso) |
| Diários dedicados | `Confirming` (CONF) e `Confirming BCP` (CONF1) — **pouco usados na prática** |
| Bancos usados na amortização | `Millennium BCP`, `Santander` |

---

## Fluxo observado (de facto)

### A) Entrada em confirming (fornecedor pago via confirming)
Lançamento em **Operações Diversas**, com referência **`PCONF/2026/0000X`**:
- **Débito** `12 Bank Suspense Account`
- **Crédito** `2789 CONFIRMING` (a dívida ao confirming aumenta)

> Nota: **não** usa "Registar pagamento" (é lançamento manual de Diversos).

### B) Amortização (o banco debita a HMD)
Movimento no diário do banco (BCP / Santander), tipicamente do **extrato**:
- **Débito** `2789 CONFIRMING` (a dívida diminui)
- **Crédito** conta de banco (`121` / `122`)
- Etiqueta tipo "Amortização de Crédito N. 39XX"; **conciliado no extrato**.

### Encargos/juros
**Não observados** como linha/contas separadas nos movimentos atuais.

---

## ⚠️ A decidir antes de transformar em tutorial de cliente

`PONTO POR VALIDAR` — O processo está recente e misto. Padronizar:
- [ ] Qual o **papel dos diários CONF / CONF1**? Usar ou descontinuar (já que o
      fluxo real passa por Operações Diversas + bancos reais)?
- [ ] A entrada é sempre por **Operações Diversas com ref `PCONF`**? Formalizar.
- [ ] Como/onde lançar **encargos e juros** do confirming (conta de gasto)?
- [ ] Validação final pela contabilidade (Sérgio/HMD).

> Quando o procedimento oficial estiver fechado, este rascunho converte-se em
> tutorial de cliente (md + PDF + Word) como os restantes.
