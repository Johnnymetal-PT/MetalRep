{
    "name": "PG Supplierinfo Purchase Button",
    "summary": "Botao 'Create RFQ' direto na lista de fornecedores do produto.",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "website": "https://www.parametroglobal.com",
    "category": "Purchases",
    "license": "LGPL-3",
    "description": """
PG Supplierinfo Purchase Button (HMD)
=====================================

a) Objetivo de negocio
----------------------
Quando o operador HMD quer pedir cotacao a um fornecedor especifico
listado no separador "Fornecedores" do produto, o standard exige sair
do produto, abrir Compras, criar PO, escolher fornecedor e produto. Com
este modulo, basta clicar "Create RFQ" na linha do fornecedor: o
sistema cria a PO com fornecedor, produto, UoM, preco, desconto, taxas
e moeda ja preenchidos a partir da linha de supplierinfo e abre o PO
para ajustar/confirmar.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `purchase` instalado.
- Studio: o XML deste modulo herda
  `studio_customization.odoo_studio_product__583c8179-...` (view Studio
  do formulario do produto) - se o cliente reset/recriar o produto em
  Studio, este XID muda e o inherit quebra. Ver FAQ.
- A linha de supplierinfo deve ter `partner_id` (fornecedor) e
  produto (`product_id` ou `product_tmpl_id`).

c) Como funciona (tecnico)
--------------------------
1. `product.supplierinfo` (`models/product_supplierinfo.py`):
   - Campo compatibilidade `purchase_requisition_id`: existe para que
     views Studio que referenciem esse campo continuem a carregar
     mesmo quando o modulo `purchase_requisition` standard nao esta
     instalado. So existe; nao tem comportamento. Manter ate o cliente
     remover essas referencias Studio.
   - `action_create_purchase_order`: monta `order_line` com produto,
     descricao (display_name + description_purchase do produto na
     lingua do fornecedor), quantidade (`min_qty` ou 1), preco
     (`price`), UoM (`product_uom` se existe, senao `uom_po_id` do
     produto, senao `uom_id`), data planeada (now + `delay` dias se
     existir), desconto, taxas. Tudo defensivo: testa
     `"discount" in self._fields` etc., porque depende de modulos
     opcionais (sale_purchase_discount etc.).
   - Decide a moeda: `currency_id` do supplierinfo (se existir o
     campo, vem de `account` ou modulos add-on), senao
     `property_purchase_currency_id` do fornecedor, senao moeda da
     empresa.
   - Cria a PO via `with_company(company)` (importante para
     multi-company) e devolve `act_window` para abrir o PO em form.

2. View (`views/product_supplierinfo_views.xml`): adiciona o botao
   "Create RFQ" antes do campo `partner_id` na list dentro de
   `seller_ids`. Visibilidade depende de o fornecedor e o produto
   estarem definidos.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_supplierinfo_purchase` na BD HMD.
2. Inventario > Artigos > abrir um produto > aba "Compra"
   ("Fornecedores" / `seller_ids`).
3. Em cada linha de fornecedor aparece o botao "Create RFQ".
4. Clicar: o sistema cria uma RFQ (PO em estado draft) com tudo
   preenchido e abre a PO no form view.
5. Ajustar (qty, prazo, condicoes), confirmar.

e) Exemplo pratico
------------------
Produto "Sofa Cliente A" tem em `seller_ids`:
  - Fornecedor "MadeiraPlus", `min_qty=10`, `price=120.00`, delay=15.
Operador abre o produto e clica "Create RFQ" na linha do MadeiraPlus.
PO criada:
  - partner = MadeiraPlus
  - linha: "Sofa Cliente A", qty 10, preco 120.00, UoM = unidade de
    compra do produto, data planeada = hoje + 15 dias.
Operador confirma a PO.

f) FAQ / Resolucao de problemas
-------------------------------
P: O botao "Create RFQ" nao aparece. Porque?
R: Possiveis causas:
   1. O XID Studio referenciado no inherit ja nao existe (o cliente
      mexeu na view do produto em Studio). Validar com Settings >
      Technical > Views.
   2. A linha nao tem `partner_id` ou nao tem `product_id`/
      `product_tmpl_id`. O `attrs` do botao esconde nesses casos.

P: "Please configure a purchase unit of measure" - erro. Resolver?
R: O produto nao tem `uom_po_id` nem `uom_id`. Configurar a unidade
   de medida de compra no produto ou no UoM standard do produto.

P: O preco vem 0. Porque?
R: A linha de supplierinfo nao tem `price`. Preencher o preco do
   fornecedor (e ate `min_qty`) antes de clicar.

P: Em multi-company, a PO foi criada para a empresa errada.
R: O modulo usa `self.company_id` da linha; se a linha nao tem
   empresa, usa `self.env.company` (a empresa atual do utilizador).
   Garantir que o supplierinfo tem `company_id` correto.

P: O campo `purchase_requisition_id` esta declarado mas nada o usa.
R: E um shim de compatibilidade para nao quebrar views Studio que
   referenciam o campo. Se o cliente parar de usar essas views, este
   campo pode ser removido com seguranca.

g) Pontos de atencao / avisos
-----------------------------
- DEPENDENCIA DE STUDIO: o XID
  `studio_customization.odoo_studio_product__583c8179-3ca5-41e1-a212-e18b0d97f25a`
  e fragil. Em upgrade do Studio ou recriacao da view, validar e
  reapontar o inherit_id.
- HARDCODED: nome do botao "Create RFQ" em ingles. Pode traduzir-se
  via .po se o cliente quiser PT.
- O `description_purchase` e concatenado a descricao do produto - se
  o operador nao quiser, alterar a linha que monta
  `product_description`.
- Em upgrade 18 -> 19, validar a assinatura de `with_company` e os
  campos opcionais (`discount`, `taxes_id`, `currency_id`,
  `product_uom`, `delay`).
""",
    "depends": ["purchase"],
    "data": ["views/product_supplierinfo_views.xml"],
    "installable": True,
    "application": False,
}
