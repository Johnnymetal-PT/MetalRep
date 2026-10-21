# Compras Mercado Nacional (MN) vs Mercado Externo (ME) — solução via Posição Fiscal

> **Objectivo:** ter controlo contabilístico separado das compras nacionais e externas do
> **mesmo** artigo, sem duplicar artigos nem categorias, e **sem quebrar o funcionamento
> normal do Odoo**.
>
> **Ambiente analisado:** Stone Trading — produção (`http://11.3.0.18:8070`,
> DB `stone-trading-mhc-main-090126`). Aplicável também à Pemaro (modelo igual).
> **Data:** 2026-07-31.

---

## 1. O problema (diagnóstico)

O erro conceptual: **o mercado (Nacional vs Externo) é uma propriedade da COMPRA, não do
ARTIGO.** O mesmo Slab pode ser comprado localmente **ou** importado. Mas:

- um `product.product` só tem **uma** categoria → não há "Slab MN" e "Slab ME" no mesmo artigo;
- a conta ME foi colocada **no artigo** (`property_account_expense_id`) **e** na categoria
  → esses artigos vão **sempre** para a conta ME, mesmo quando comprados no mercado nacional.
  É o **oposto** do pretendido.

### Números que comprovam (Stone prod)

| Facto | Valor |
|---|---|
| `product.template` com conta de gasto **forçada no artigo** | **175** |
| … dos quais forçam contas ME | ex.: 29× `21123 Mercadorias ME`, 5× `6321422 ME N/Ded`, 2× `32623 ME` |
| Categoria "Mercadoria Externo" | 41 artigos |
| Categoria "Mercadoria Nacional" | 1 artigo |
| Categorias MN/ME de matéria-prima e auxiliares | **0 artigos** (criadas mas não usadas) |

**Regra do Odoo para a conta de gasto:** conta do artigo
(`property_account_expense_id`, definida em `product.template`) → se vazia, usa a da categoria
(`property_account_expense_categ_id`). A do artigo **prevalece** sobre a da categoria.

---

## 2. A peça que falta (e já está 90% montado)

Já existem **posições fiscais** a funcionar:

| Posição fiscal | Auto | Mapa de impostos | Mapa de contas |
|---|---|---|---|
| **Domestic regime** (país = Moçambique) | ✅ | base (16%) | — |
| **Import/Export** | ✅ | ✅ `16% → Isento / 0% Import` | ❌ **VAZIO** |

A posição **Import/Export já troca o imposto** automaticamente nas importações — **mas não
troca a conta**. Falta **preencher o mapeamento de contas** dessa posição fiscal. É só isso.

> Doc oficial Odoo: *"Account mapping is based on the income and expense accounts defined on
> the product or product category… particularly useful for distinguishing between national
> and import purchases of the same product."*

---

## 3. A solução (nativa, recomendada)

**Princípio: 1 artigo → 1 categoria neutra (conta MN por defeito). A importação é tratada
pela posição fiscal (impostos + contas).**

```
                          COMPRA a fornecedor NACIONAL          COMPRA a fornecedor EXTERNO
                          (Posição fiscal: Domestic)            (Posição fiscal: Import/Export)
   Artigo "Slab Granito"
   Categoria "Mercadoria" ──► conta 21111 (MN 16%)  ────►       conta 21123 (ME Isento)  ← remapeada
   (conta base = 21111)       imposto IVA 16%                   imposto 0% Import        ← já feito
```

O mesmo artigo, **uma só categoria**, cai na conta certa e no imposto certo **conforme o
fornecedor**, automaticamente. As contas MN (`21111`) e ME (`21123`) continuam **separadas**
no razão/balancete — logo, mantém-se o controlo pretendido — mas agora reflectem a **compra
real**, não uma etiqueta fixa no produto.

### 3.1. Mapeamento de contas a acrescentar na posição fiscal *Import/Export*

Uma linha por par (Conta no produto → Conta a usar):

| Conta no produto (MN) | → Conta a usar (ME) |
|---|---|
| `21111` Mercadoria MN IVA 16% | `21123` Mercadorias ME Isento |
| `212111` Matérias primas MN 16% | `212123` Matérias primas ME Isento |
| `212211` Matérias auxiliares MN 16% | `212222` Matérias auxiliares ME N/Ded |
| `6321411` Ferramentas MN 16% | `6321422` Ferramentas ME N/Ded |
| *(transportes e outras contas — decidir os pares MN→ME)* | |

> O mapa de **impostos** já está feito na Import/Export (`16% → Isento / 0% Import`).
> Só falta o mapa de **contas** acima.

---

## 4. Plano de migração (estado actual → modelo limpo)

1. **Completar o mapa de contas** na posição fiscal Import/Export (pares MN→ME da secção 3.1).
2. **Passar os 41 artigos "Mercadoria Externo" → categoria neutra** (base MN).
3. **Limpar o override no artigo** (`property_account_expense_id`) nos que forçam contas ME
   → passam a herdar a conta MN da categoria.
4. **Garantir a posição fiscal nos fornecedores**:
   - 68 já têm "Domestic regime", 9 têm "Import/Export", **102 sem posição** (auto ou por atribuir);
   - os fornecedores externos têm de apanhar "Import/Export" (por país/auto-aplicar ou manual).
5. **Categorias "…Externo"** tornam-se redundantes → manter só se algum artigo for
   *exclusivamente* importado; caso contrário, arquivar.

> **Importante:** isto é **para a frente**. Lançamentos já feitos nas contas ME ficam como estão.

---

## 5. Porque é esta a via correcta

- É o mecanismo **nativo** do Odoo (posição fiscal = adaptar impostos **e** contas por
  cliente/fornecedor). **Não** precisa de módulo nem de personalização.
- O override de conta **no artigo** é precisamente o que "luta" contra o Odoo — remove-se.
- O controlo MN/ME fica **melhor**: baseado na compra real, não numa etiqueta estática.
- Alternativas piores rejeitadas:
  - **Duplicar artigos (MN/ME):** parte o stock do mesmo bem físico em dois. ✗
  - **Duas categorias e trocar por compra:** impossível — a categoria está no artigo, não na
    linha da compra. ✗
  - **(Opcional) Contabilidade analítica** pode dar uma dimensão extra de controlo, mas **não
    substitui** a segregação de contas; é complementar, não necessária.

---

## 6. Próximos passos / decisões

- [ ] Confirmar o modelo **"categoria neutra + posição fiscal"** (recomendado).
- [ ] **Protótipo na TESTE (8074):** completar o mapa de contas da Import/Export e fazer 2
      compras do mesmo artigo (uma nacional, uma externa) para validar que caem nas contas
      certas automaticamente — **sem tocar na produção**.
- [ ] Decidir os **pares MN→ME** para transportes e outras contas que hoje estão no artigo
      (mercadoria/matéria-prima/auxiliares já são óbvios).
- [ ] Depois de validado na teste → replicar em produção (Stone e Pemaro).

---

---

## 7. DECISÃO FINAL (2026-08-02)

**Requisito confirmado:** contas GL separadas por mercado (`21111` MN vs `21123` ME, etc.) é
**exigência legal/contabilística**, não apenas controlo. E o mesmo artigo é comprado dos
**dois** mercados.

**Investigação esgotada:** não existe módulo OCA nem do Apps Store, mantido para Odoo 18, que
troque a conta de valorização/entrada de stock pela posição fiscal. O único parecido
(`account_fiscal_position_rule_stock`, OCA) ficou nas versões antigas (8.0–12.0) e não foi
migrado. O padrão continental/SNC confirma a legitimidade de segregar compras/existências por
conta.

**Via escolhida:** módulo custom **`mh_market_stock`** (em
`custom-addons/ubuntu_server/mh_market_stock/`), porque:
- as vias nativas não separam contas GL no cenário dual-mercado;
- não há alternativa pronta.

### Arquitectura (implementada)
- Override de `stock.move._get_accounting_data_for_valuation()`.
- Determina a posição fiscal do movimento (PO → devolução herda do original → fornecedor manual).
- Aplica o **mesmo mapa de contas** da posição fiscal às contas de **entrada/saída** de stock.
- **Não** remapeia a conta de **valorização** (o activo `223` é o mesmo bem).
- Fonte única de verdade = mapa de contas da posição fiscal. Mapa vazio → módulo inerte.

### Configuração necessária
1. Completar o **Mapeamento de Contas** da posição fiscal *Import/Export* com os pares MN→ME.
2. Garantir a posição fiscal *Import/Export* nos fornecedores externos.

### Plano de teste (8074) — antes de produção
- Ciclo A (nacional): PO → recepção → factura → `21111` fecha a zero.
- Ciclo B (importação): PO externa → recepção → factura → `21123` fecha a zero.
- Ciclo C (devolução de B): sem saldo pendurado.
- Ciclo D (landed cost em B): vai à `223`, não estraga o mapeamento.

> Detalhe: ver `custom-addons/ubuntu_server/mh_market_stock/README.md`.

---

## Referências

- Fiscal positions (tax and account mapping) — Odoo 18.0:
  https://www.odoo.com/documentation/18.0/applications/finance/accounting/taxes/fiscal_positions.html
- Fiscal positions — Odoo 16.0:
  https://www.odoo.com/documentation/16.0/applications/finance/accounting/taxes/fiscal_positions.html
- Can stock valuation be changed by Fiscal Position — Odoo Forum:
  https://www.odoo.com/forum/help-1/can-stock-valuation-be-changed-by-fiscal-position-269264
- OCA/account-fiscal-rule (histórico account_fiscal_position_rule_stock):
  https://github.com/OCA/account-fiscal-rule
