{
    "name": "HMD Sale Price Calculator",
    "version": "18.0.1.0.2",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "category": "Sales",
    "summary": "Calculadora de preco por linha de venda: custo (com fallback) + margem fixa/percentual.",
    "license": "LGPL-3",
    "description": """
HMD Sale Price Calculator
=========================

a) Objetivo de negocio
----------------------
O comercial HMD precisa de orcamentar com margem coerente e
rastreavel. O standard nao mostra o custo do produto no orcamento e
nao guarda historico da margem aplicada. Este modulo adiciona um
botao "Calculadora" em cada linha de venda que:
  - obtem o custo do produto (com varios fallbacks: standard_price ->
    ultima PO -> BoM);
  - permite definir margem em montante fixo ou percentagem;
  - calcula o preco resultante e escreve em `price_unit`;
  - guarda na linha custo, tipo/valor de margem, montante calculado e
    observacoes do utilizador (visiveis nas listas).

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `sale`, `purchase`, `mrp` (BoMs).
- Produtos com `standard_price` configurado, OU historico de PO, OU
  BoM definida - qualquer um dos 3 e suficiente. Sem nenhum, o custo
  vem 0 e a calculadora avisa.

c) Como funciona (tecnico)
--------------------------
1. `sale.order.line` (`models/sale_order_line.py`):
   - 5 campos novos: `calculator_cost_price`,
     `calculator_margin_type` (selection fixed/percent),
     `calculator_margin_value`, `calculator_margin_amount`,
     `calculator_observation` (Text).
   - `_get_calculator_cost()`: pipeline de fallbacks na ordem:
       1. `product.standard_price` (variante, depois template);
       2. `_get_latest_purchase_price`: ultima PO line com state
          purchase/done para o produto, ordenado por
          `date_planned desc, id desc`; converte UoM e moeda se
          necessario;
       3. `_get_bom_cost`: percorre as linhas da BoM mais antiga
          aplicavel a variante (respeitando
          `bom_product_template_attribute_value_ids`), obtem custo
          de fornecedor de cada componente
          (`_get_component_supplier_cost`), pondera pela qty e
          divide pela `bom_qty`.
   - `action_open_price_calculator`: abre o wizard com defaults a
     partir do estado atual da linha.

2. `sale.order.line.price.calculator` (TransientModel, em
   `wizard/sale_order_line_price_calculator.py`):
   - Campos: `cost_price`, `margin_type`, `margin_value`,
     `margin_amount` (computed), `computed_price` (computed),
     `observation`.
   - `_compute_margin_amount`: percent -> margem sobre PV
     `cost * m / (1 - m)` (PV = `cost / (1 - m)`); fixed -> `value`.
   - `_compute_computed_price`: `cost + margin_amount`.
   - `action_apply`: escreve na linha de venda os 5 campos custom
     mais `price_unit = computed_price`.

3. Views (`views/sale_order_views.xml`):
   - Botao "Calculadora" (icon fa-calculator) na list de linhas no
     SO form e na sub-form.
   - Group "Price Calculator" na sub-form com os 5 campos custom
     read-only (so para visualizar o que o wizard escreveu).
   - Coluna `calculator_observation` na list, optional show.
   - Botao tambem na view standard partilhada `sale.view_order_line_tree`
     (escondido em linhas section/note e em SOs nao-draft).

d) Passo a passo de utilizacao
------------------------------
1. Garantir que o produto tem custo conhecido (standard_price, PO
   anterior, ou BoM).
2. Instalar `hmd_sale_price_calculator`.
3. Vendas > Orcamentos > criar/abrir.
4. Adicionar uma linha com produto.
5. Clicar no icon calculadora na linha (ou na sub-form).
6. O wizard abre com:
     - `cost_price` pre-preenchido pelo pipeline de fallback;
     - `margin_type` "Montante Fixo" (default), com `margin_value` 0.
7. Escolher tipo: Fixo (introduzir EUR) ou Percentagem (introduzir
   %).
8. Adicionar observacao (opcional).
9. "Calcular" -> escreve `price_unit` e guarda o calculo na linha.

e) Exemplo pratico
------------------
Linha: produto "Sofa Lara", `standard_price = 480`.
Wizard:
  - cost_price = 480
  - margin_type = percent (margem s/ PV)
  - margin_value = 35
  - margin_amount = 480 * 0.35 / (1 - 0.35) = 258.46
  - computed_price = 480 / (1 - 0.35) = 738.46
Calcular -> `price_unit = 738.46`; `calculator_*` guardam o calculo;
observacao "Margem padrao linha tecido 2026" guardada na linha.

Outro caso: produto sem standard_price, mas com BoM:
  Componentes via supplierinfo + qty = 312 EUR
  bom_qty = 1
  -> custo = 312 EUR

f) FAQ / Resolucao de problemas
-------------------------------
P: O custo veio 0. Porque?
R: Nem standard_price, nem PO previa, nem BoM existem ou tem
   fornecedor de custo. Preencher pelo menos um.

P: O custo da PO veio em USD mas a venda e em EUR. Como?
R: `_convert_to_target_currency` faz a conversao automaticamente na
   data da PO (`date_planned`) usando `_convert` standard. Verificar
   se ha taxas de cambio na BD para o periodo.

P: A linha tem variantes com PTAVs. A BoM correta e escolhida?
R: `_get_bom_cost` filtra `bom_product_template_attribute_value_ids`
   pelas PTAVs da variante. Linhas que tenham PTAVs nao presentes na
   variante sao saltadas.

P: O preco volta a ser recalculado quando muda a quantidade?
R: NAO. O calculo da margem aplica-se ao `price_unit` (preco
   unitario). Quantidade nao re-dispara o wizard - tem de se voltar
   a abrir.

P: Como ver o calculo aplicado a posteriori?
R: Na sub-form da linha, secao "Price Calculator" - todos os campos
   estao read-only.

P: Os clientes querem ver a observacao na cotacao impressa?
R: O campo `calculator_observation` esta na linha. Adaptar o template
   QWeb de fatura/orcamento para incluir.

g) Pontos de atencao / avisos
-----------------------------
- `_get_latest_purchase_price` filtra state in ['purchase', 'done'] -
  ignora RFQs e canceladas. Se quiser incluir RFQ, alterar.
- O `_get_bom_cost` divide o custo total pelo `bom_qty` para obter
  custo unitario. Se o produto tem BoM por lote (ex.: 100 unidades),
  o calculo e correto.
- Conversao de moeda usa a taxa do dia da PO, nao a do SO. Mudar
  para `order.date_order` se for politica HMD diferente.
- A sub-form group "Price Calculator" expoe os campos custom a todos
  os utilizadores com leitura ao SO. Se for sensivel, restringir por
  grupo.
- O botao em `sale.view_order_line_tree` so esta visivel em
  rascunhos (`parent.state == 'draft'`) - quando o SO esta confirmado
  desaparece. Mudar `attrs` se for preciso recalcular post-confirmacao.
""",
    "depends": ["sale", "purchase", "mrp"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/sale_order_line_price_calculator_views.xml",
        "wizard/sale_order_line_components_calculator_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
}
