# mh_market_stock — Contas de stock por mercado (Nacional vs Externo)

Faz a distinção **Mercado Nacional (MN) vs Mercado Externo (ME)** cair em contas GL
separadas, de forma automática, **sem duplicar artigos nem categorias**, usando a
**posição fiscal** como única fonte de verdade — incluindo o lado da **valorização de
stock**, que o Odoo standard não cobre.

## O problema

Num artigo comprado nos dois mercados, o Odoo standard trata mal a valorização:

- A **posição fiscal** remapeia a conta da **factura** (ex.: `21111 → 21123` para importação).
- Mas a **valorização de stock** (recepção) lê a conta **só da categoria** e **ignora** a
  posição fiscal.

Resultado: a factura vai para `21123` (ME) e a recepção fica em `21111` (MN) → a conta-ponte
de **entrada de stock nunca fecha a zero** (des-sincroniza compra ↔ valorização).

Limitação conhecida do Odoo standard: a posição fiscal **não** toca nas contas de stock. Não
existe módulo OCA/Apps mantido para 18.0 que resolva isto.

## A solução — 1) contas de stock seguem a posição fiscal

O módulo **alinha a conta de entrada de stock com a posição fiscal da compra**, aplicando o
**mesmo mapa de contas** que a factura já usa:

```
Recepção (importação):  Dr 223 Existências  100.000 / Cr 21123 (entrada ME)  ← remapeada
Factura   (importação):  Dr 21123 (ME)      100.000 / Cr Fornecedor          (0% import)
→ 21123 fecha a zero ✅   |   contas GL MN e ME separadas   |   1 artigo, 1 categoria
```

- **Fonte única de verdade:** o mapa de contas da posição fiscal (`account.fiscal.position`
  → separador *Mapeamento de Contas*). Se o mapa estiver **vazio**, o módulo é **inerte**.
- A conta de **valorização** (o activo, ex.: `223`) **não** é remapeada — o bem é o mesmo,
  venha de que mercado vier. Só a conta de **entrada/compra** muda.

### Modelo BIDIRECCIONAL (dispensa migrar produtos)

Como os produtos podem ter base **MN** ou **ME** (categoria "Nacional" ou "Externo"),
configuram-se **dois** mapas ortogonais:

| Posição fiscal | Mapa | Serve |
|---|---|---|
| **Import/Export** | MN → ME (ex.: `21111→21123`) | produto base MN comprado a **fornecedor externo** |
| **Domestic** | ME → MN (ex.: `21123→21111`) | produto base ME comprado a **fornecedor nacional** |

Os dois mapas **nunca colidem** (a Domestic só mexe em contas ME, a Import/Export só em contas
MN). As 4 combinações (base MN/ME × fornecedor nacional/externo) caem na conta certa — e a
**migração de produtos "Externo"→"Nacional" deixa de ser necessária**.

> Nota de assimetria: se duas contas MN colapsarem numa só ME no forward (ex.: transporte
> `2124111` e `2124113` → `2124123`), o inverso só pode devolver a **uma** MN (uma origem só
> tem um destino numa posição fiscal) — escolhe-se a de **16%**. Por isso o forward pode ter
> mais um par que o inverso.

## A solução — 2) automatismo da posição fiscal do parceiro

Para as compras/vendas apanharem a posição fiscal certa, o módulo **carimba automaticamente**
`property_account_position_id` no parceiro (`res.partner`):

- Ao **criar** o parceiro ou **mudar o país**, usa a auto-detecção nativa do Odoo
  (`account.fiscal.position._get_fiscal_position`) — o parceiro fica com exactamente a mesma
  posição fiscal que o documento detectaria.
- **Só** quando o campo está **vazio** (respeita a escolha manual) e **só** quando há **país**.
- Aplica a **clientes e fornecedores**; ignora contactos filhos.
- Depende de as posições fiscais terem `auto_apply` bem configurado (Domestic = país da
  empresa; Import/Export = catch-all sem país).

## Como funciona (técnico)

**Valorização** — override de `stock.move._get_accounting_data_for_valuation()`:

1. Determina a posição fiscal do movimento (`_market_fiscal_position`), por esta ordem:
   - Ordem de compra (`purchase_line_id.order_id.fiscal_position_id`);
   - Devolução → herda do movimento original (`origin_returned_move_id`);
   - Recepção manual de fornecedor → posição fiscal do parceiro (só `supplier_rank > 0`).
2. Aplica `fiscal_position.map_account()` às contas de **entrada/saída** (`acc_src`, `acc_dest`).
3. Deixa a conta de **valorização** intacta.

Só remapeia as contas que **têm par** no mapa da posição fiscal; as restantes passam iguais.
Vendas e devoluções de clientes **não** são afectadas (contexto não-fornecedor).

**Parceiro** — override de `res.partner.create()` e `write()` (`_mh_apply_auto_fiscal_position`).

## Configuração necessária

1. Preencher o **Mapeamento de Contas** das posições fiscais:
   - **Import/Export**: pares MN→ME (`21111→21123`, `212111→212123`, `212211→212222`,
     `2123211→2123222`, transportes, corte, `6321411→6321422`, …).
   - **Domestic**: os pares inversos ME→MN.
2. Garantir `auto_apply` nas posições fiscais (Domestic = país da empresa; Import/Export = sem
   país). Fazer o **backfill** da FP nos parceiros existentes (script `backfill_fp*.py`).
3. *(À parte do módulo)* pôr **imposto de compra 16% por defeito** nos produtos "Externo",
   senão uma compra nacional fica sem IVA (o mapa trata da conta, não do imposto).

## Casos cobertos / a vigiar

- ✅ Mesmo artigo comprado nacional e importado (conta de entrada fecha a zero em cada mercado).
- ✅ Produto "Externo" (base ME) comprado a fornecedor nacional → cai em MN (mapa inverso).
- ✅ Devoluções ao fornecedor (herdam a posição fiscal do movimento original).
- ✅ Landed costs (entram na conta de valorização, não remapeada → compatível).
- ⚠️ Reavaliações PMC: usam a conta de valorização (não remapeada) → validar em teste.

## Dependências

`stock_account`, `purchase_stock` (traz `account` transitivamente para `res.partner`/FP).

## Estado

Validado na teste (ciclos: compra nacional / importada / devolução / landed cost / compra
nacional de produto Externo). Em produção na Stone e Pemaro (Moçambique). **Não aplicável** ao
EQS (sem plano MN/ME) nem ao Padrão (Portugal/SNC).

Ver também: `SOLUCAO_MERCADO_NACIONAL_EXTERNO_POSICAO_FISCAL.md` (raiz do repo Stone).
