# MH SAF-T (MZ) — `mh_saft`

Módulo de **facturação para a Autoridade Tributária de Moçambique (AT)**: um mapa
interactivo "Vendas AT" e a exportação do ficheiro (SAF-T MZ / comunicação de
facturas), a partir das facturas de venda do Odoo.

> **v0** — âmbito **facturação** (SalesInvoices). O ficheiro plano (Excel/CSV) segue
> o formato "Vendas AT" do PHC; o XML segue o modelo PALOP (PT/AO). Ver **Pendentes**.

---

## 1. O que faz

- **Menu:** *Contabilidade → Relatórios → Autoridade Tributária (AT) → Vendas AT (SAF-T)*.
- **Mapa interactivo** (client action OWL, à imagem do `mh_stock_at_date`): mostra as
  facturas de venda **validadas** de um período (**Ano / Mês**), **linha a linha**,
  no formato do ficheiro "Vendas AT".
- **Export** (botão *Exportar* + selector de formato): **xlsx** (folha protegida),
  **csv** e **xml** (SAF-T modelo PALOP).

Só entram documentos **`posted`** (rascunhos e cancelados são excluídos), da **empresa
activa** e do **período** escolhido.

---

## 2. Formato "Vendas AT" (12 colunas, uma linha por LINHA de factura)

| Coluna | Fonte no Odoo |
|---|---|
| `data` | `move.invoice_date` (formato `dd-Mmm-aa`, ex. `01-Jun-26`) |
| `documento` | **série** = código do prefixo da sequência sem o ano (`FT/2026/` → `FT`; `RFT` p/ NC; `DFT` p/ ND) |
| `número` | `move.sequence_number` |
| `nuit` | `partner.vat` |
| `nome_do_cliente` | `partner.name` |
| `designação` | `line.name` (descrição da linha) |
| `preço_unitário` | `line.price_unit` |
| `total_linha` | `line.price_subtotal` (base da linha) |
| `iva` | taxa % da primeira `line.tax_ids` (16 / 0) |
| `total_ilíquido` | `move.amount_untaxed` (base do **documento**, repetido) |
| `valor_iva` | `move.amount_tax` (repetido) |
| `total` | `move.amount_total` (repetido) |

Valores monetários formatados em **MT** (separador de milhares).

---

## 3. Tipos de documento (SAF-T) e séries

`_saft_type()` classifica cada documento:

| Tipo | Condição Odoo | Série (`documento`) |
|---|---|---|
| **FT** (Factura) | `out_invoice` sem `debit_origin_id` | `FT` |
| **ND** (Nota de Débito) | `out_invoice` **com** `debit_origin_id` (via `account_debit_note`) | `DFT` |
| **NC** (Nota de Crédito) | `out_refund` | `RFT` |

**Notas de débito → `DFT` automático:** depende de uma peça no **`mh_account`**
(`account.move._get_last_sequence_domain`) que segrega as notas de débito no seu
próprio fluxo `DFT`, e do módulo standard **`account_debit_note`** (com o
`debit_sequence` activo no diário de facturas). Sem essa peça, as notas de débito
saem na série `FT` das facturas. Ver o `NUMERACAO.md`/`account_move.py` do `mh_account`.

---

## 4. Geração do XML SAF-T (`generate_saft_xml`)

XML no modelo PALOP: `Header` + `MasterFiles` (não usado na v0 plana) +
`SourceDocuments/SalesInvoices` com `Invoice` (nº, data, tipo, cliente, `Line`,
`DocumentTotals`). **Reservado para o SAF-T completo** — pendente do XSD oficial da AT
e da assinatura/`Hash` + certificação.

---

## 5. Ficheiros

```
mh_saft/
├── __manifest__.py
├── models/saft_report.py         # AbstractModel report.mh_saft.report (mapa + export + xml)
├── controllers/main.py           # /mh_saft/export → xlsx (protegido) / csv / xml
├── reports/saft_templates.xml     # QWeb do mapa (tabela plana estilizada, cabeçalho fixo)
├── static/src/js/saft_report.js   # client action OWL (filtros Ano/Mês/Tipo + Exportar)
├── static/src/js/saft_report.xml  # template OWL
├── data/client_action.xml         # ir.actions.client
└── views/menus.xml                # secção "Autoridade Tributária (AT)" + "Vendas AT (SAF-T)"
```

**Dependências:** `account`, `web`. (Funciona melhor com `account_debit_note` instalado,
para as notas de débito; usa `getattr` defensivo se não estiver.)

---

## 6. Base legal (MZ)

- Aviso nº /AT/DGI/2025 (27/03/2025); Código do IVA (Lei 32/2007, alt. Lei 22/2022).
- Submissão **mensal** na plataforma **e-Declaração** (XML/CSV).
- Software de facturação sujeito a **certificação pela ATM**.

---

## 7. Pendentes (dependem da AT)

1. **XSD/versão oficial** do schema SAF-T (MZ) — aqui usa-se o modelo PALOP.
2. **Assinatura/`Hash` das facturas + certificação ATM** — o `Hash` sai **vazio** na v0.
3. Mapeamento dos **códigos de IVA** (`NOR`/`ISE`) é heurístico — afinar à tabela oficial.

---

## 8. ⚠️ NOTA — menus fiscais ocultados no `account_MZ`

Ao criar a secção **"Autoridade Tributária (AT)"**, **ocultámos 4 menus** do `account_MZ`
que estavam soltos sob *Relatórios* (pô-los `active=False` em
`account_MZ/views/menus.xml`):

- **Modelo 19** (`account_MZ.menu_payment_register`)
- **M20/H** (`account_MZ.report_m20`)
- **M11** (`account_MZ.menu_modelo11`)
- **Relação Nominal** (`account_MZ.menu_my_custom_module_name_relations`)

**Isto é reversível e NÃO apaga nada** (só esconde o menu; as acções/relatórios mantêm-se).

**A FAZER / decisão em aberto:** decidir o destino final destes 4 —
- **(a)** mantê-los ocultos (como está), ou
- **(b)** **movê-los para dentro** da secção *Autoridade Tributária (AT)* (reparenting
  para `mh_saft.menu_at_section`), ficando todas as obrigações à AT num só sítio, ou
- **(c)** reativá-los (`active=True`).

> Para **reactivar**: pôr `active=True` (ou remover os 4 `<record>` no `account_MZ/views/menus.xml`)
> e `-u account_MZ`.

Aplicado nas duas empresas (Stone e Pemaro).
