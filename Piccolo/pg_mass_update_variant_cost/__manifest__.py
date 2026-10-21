# -*- coding: utf-8 -*-
{
    "name": "PG Update Mass variants",
    "version": "17.0",
    "category": "Sale",
    "summary": "Modulo terceiro (INKERP, OPL-1) que adiciona um wizard para atualizar o cost price em multiplas variantes de produto de uma so vez.",
    "author": "INKERP",
    "website": "http://www.inkerp.com/",
    "depends": ["product"],
    "data": [
        "views/product_product_view.xml",
        "security/ir.model.access.csv",
        "wizard/mass_update_variant_cost_wizard.xml",
    ],
    "description": """
PG Mass Update Variant Cost (vendored - terceiro)
=================================================

NOTA SOBRE ESTE MODULO
----------------------
- **Origem**: INKERP (`http://www.inkerp.com/`).
- **Licenca**: OPL-1 (paga).
- **Status no projeto Piccolo**: vendored - codigo do
  fornecedor; manter na pasta sem alteracoes.

a) Objetivo de negocio
----------------------
Atualizar em massa o ``standard_price`` (custo) de varias
variantes de produto a partir de um wizard simples, sem ter de
abrir cada variante individualmente.

b) Pre-requisitos
-----------------
- Modulo standard ``product``.
- Licenca paga ativa.

c) Como funciona (resumo)
-------------------------
- Acrescenta entrada de menu/botao em variantes.
- Wizard recebe lista de variantes selecionadas + novo cost
  price -> escreve em ``standard_price``.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Selecionar varias variantes na lista (multi-select).
3. Action menu > "Mass Update Variant Cost".
4. Introduzir novo custo -> Confirmar.

e) Exemplo pratico
------------------
Catalogo com 50 variantes de "Cadeira X" (uma por cor). O
fornecedor sobe o custo do casco em 5 EUR. Selecionar todas as
50, abrir o wizard, escrever 35 EUR -> custo atualizado para
as 50 num clique.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Wizard nao aparece"* -> module nao instalado ou licenca
  invalida.
- *"Custo nao atualiza alguma variante"* -> sem direitos de
  escrita em ``product.product`` para o utilizador atual.

g) Pontos de atencao / avisos
-----------------------------
- **NAO editar codigo do modulo**. Em update, perdem-se as
  alteracoes locais.
- Confirmacao do user e definitiva - sem dry-run. Validar
  selecao antes de confirmar.
""",
    "images": ["static/description/banner.png"],
    "license": "OPL-1",
    "installable": True,
    "application": True,
    "auto_install": False,
}
