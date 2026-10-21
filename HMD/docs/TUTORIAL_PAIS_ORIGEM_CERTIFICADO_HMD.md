# Tutorial — País de Origem nas linhas da fatura (Certificado de Origem) (HMD)

> Guia rápido para garantir que o **país de origem** aparece em **todas as
> linhas** da fatura, requisito para emitir o **Certificado de Origem**.
> O campo usado é o **"País do Produto"** (campo Intrastat standard do Odoo 18),
> impresso no relatório **"Faturas (multi-via) Completas"**.

---

## 1. O problema (e a causa)

O Certificado de Origem só pode ser emitido quando **o país de origem está
preenchido em todas as linhas** da fatura.

No relatório **"Faturas (multi-via) Completas"** a coluna **"País do Produto"**
é impressa **linha a linha**. Se o campo estiver preenchido só em algumas
linhas, o país de origem aparece apenas nessas — as restantes saem em branco e
o certificado não pode ser emitido.

**Causa:** as linhas em branco não têm o campo **"País do Produto"** preenchido.
Não é uma falha do sistema — é um campo que ficou por preencher.

---

## 2. A solução rápida — preencher na fatura (mesmo já confirmada)

Foi adicionado um separador **"Intrastat"** no formulário da fatura, que permite
preencher o país de origem **mesmo com a fatura já confirmada**, sem desbloquear
preço, conta ou quantidade.

1. Abre a fatura em **Contabilidade → Clientes → Faturas**.
2. Selecciona o separador **"Intrastat"** (ao lado de "Linhas da Fatura").
3. Na coluna **"País do Produto"**, escolhe o país de origem em **todas as
   linhas** — não deixes nenhuma em branco.
   - Podes também preencher, na mesma vista, o **"Intrastat"** e o **"Código HS"**
     se forem necessários.
4. **Guardar**.
5. Reimprime o documento **"Faturas (multi-via) Completas"**
   (**Imprimir → Faturas (multi-via) Completas**). A coluna **"País do Produto"**
   passa a sair em todas as linhas → o Certificado de Origem já pode ser emitido.

> **Nota importante:** o preço, a conta e a quantidade **não** são editáveis
> neste separador. Só se editam os três campos Intrastat (País do Produto,
> Intrastat e Código HS). É seguro fazê-lo numa fatura confirmada.

---

## 3. Evitar o problema no futuro — verificar e preencher no produto

Para não ter de preencher linha a linha de cada vez, define os dados Intrastat
**na ficha do produto**. Estão dois campos relevantes, ambos na mesma secção:

- **País de Origem** (*Country of Origin*) — o país de origem da mercadoria;
- **Código de Mercadoria** (*Commodity Code*, código NC/HS) — o código
  pautal usado no Intrastat e no Código HS da linha.

### 3.1. Onde estão os campos no produto

1. Vai a **Inventário → Produtos → Produtos** (ou **Vendas → Produtos →
   Produtos**) e abre o produto.
2. Seleciona o separador **"Faturação"** (*Invoicing*).
3. Na secção **"Contabilidade"**, encontras o grupo **"Intrastat"** com:
   - **Código de Mercadoria** — o código pautal do artigo;
   - **País de Origem** — o país onde o produto é originário.
4. Preenche os dois campos e **Guarda**.

> Se o produto tiver **várias variantes**, o grupo Intrastat aparece ao nível de
> cada variante — abre a variante e preenche lá.

### 3.2. Verificar vários produtos de uma vez (opcional)

Para rever muitos produtos rapidamente, na lista de produtos ativa as colunas
**"Código de Mercadoria"** / **"País de Origem"** (menu de colunas opcionais, no
canto superior direito da lista) e confirma quais estão em branco. A lista de
produtos permite edição em linha para corrigir vários de seguida.

### 3.3. O que acontece nas faturas a partir daí

- O **Código HS** da linha (**"Código HS"**) herda **sempre** o Código de
  Mercadoria do produto — podendo corrigir-se por linha.
- O **País do Produto** da linha herda o País de Origem do produto **apenas
  quando a fatura está em contexto Intrastat** (cliente de país que ativa
  Intrastat). Fora desse contexto — típico numa **exportação** que precisa de
  Certificado de Origem — o campo **pode não ser preenchido automaticamente**,
  mesmo com o produto configurado.

> **Por isso:** preencher o produto ajuda e é boa prática, mas antes de emitir o
> Certificado de Origem confirma **sempre** que o **"País do Produto"** está
> preenchido em **todas as linhas** da fatura (secção 2). Preencher o produto
> reduz o trabalho manual, mas não substitui a verificação final na fatura.

---

## 4. Resumo

| Situação | O que fazer |
|---|---|
| Fatura já confirmada, faltam linhas com país | Separador **"Intrastat"** → preencher **"País do Produto"** em todas as linhas → reimprimir |
| Fatura em rascunho | Preencher **"País do Produto"** nas linhas antes de confirmar |
| Evitar repetir sempre | Preencher **País de Origem** e **Código de Mercadoria** na ficha do produto (separador Faturação → Intrastat) |
| Antes de emitir o certificado | Confirmar **sempre** que o "País do Produto" está em **todas** as linhas — a herança do produto nem sempre preenche |

---

## 5. Notas técnicas (para consultores)

- **Linha da fatura** (standard, `account_intrastat` Enterprise):
  - `account.move.line.intrastat_product_origin_country_id` — rótulo "País do
    Produto"; `store=True, readonly=False`;
  - herança: `_compute_origin_country` só preenche
    `= move_id.intrastat_country_id and product_tmpl_id.intrastat_origin_country_id`
    — ou seja, **só herda do produto quando a fatura tem `intrastat_country_id`**
    (contexto Intrastat). Fora disso fica vazio e é preenchido à mão.
    (`vendor/odoo_src/enterprise/account_intrastat/models/account_move.py:52-57`)
- **Produto** (standard): `product.template.intrastat_origin_country_id`
  ("Country of Origin") e `intrastat_code_id` ("Commodity Code"), no separador
  Faturação → grupo Intrastat
  (`vendor/odoo_src/enterprise/account_intrastat/views/product_view.xml:9-25`).
- **Relatório**: `fatura_completa.xml` — coluna condicional
  (`display_origin = any(l.intrastat_product_origin_country_id ...)`), impressa
  por linha.
- **Separador "Intrastat" na fatura**: módulo custom `pg_account_intrastat_hs_code`
  (tarefa 5734), via One2many dedicado `pg_intrastat_line_ids`, que expõe apenas
  País do Produto, Intrastat e Código HS como editáveis — inclusive em faturas
  publicadas. O `pg_intrastat_code_id` (Código HS) da linha herda **sempre** o
  `intrastat_code_id` do produto (compute só depende de `product_id`).
