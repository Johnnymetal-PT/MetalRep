{
    "name": "PG Product Duplicate Scanner",
    "version": "17.0.1.0.0",
    "author": "Parametro Global",
    "category": "Inventory",
    "summary": "Deteta produtos com barcode ou referencia interna duplicados.",
    "description": """
PG Product Duplicate Scanner
============================

a) Objetivo de negocio
----------------------
Identificar rapidamente produtos com codigo de barras (`barcode`) ou referencia
interna (`default_code`) duplicados. Duplicados causam falhas em importacoes,
problemas em POS e em integracoes, por isso o objetivo e ter uma forma simples
de listar todos os duplicados em tempo de manutencao.

b) Pre-requisitos
-----------------
- Modulo standard `product` instalado.
- Acesso ao menu Inventario / Produtos para acionar o botao manual.
- Acesso aos logs do servidor para consultar o detalhe dos duplicados.

c) Como funciona
----------------
- Heranca em `models/product_template_duplicates.py`:
  - Adiciona o metodo `action_log_duplicate_barcodes_and_codes` ao
    `product.template`.
  - Faz um `search` em todos os templates com `barcode` preenchido, agrupa por
    valor de barcode e regista no log do servidor (warning) os grupos com mais
    do que um template.
  - Faz o mesmo exercicio para `default_code`.
  - Devolve uma notificacao Odoo (display_notification) com o resumo do numero
    de grupos duplicados encontrados.
- `views/product_template_duplicate_scan.xml`: adiciona o botao "Scan
  Duplicates" no header da vista form do `product.template`.
- `data/server_action_duplicate_scan.xml`: regista uma `ir.actions.server`
  para o mesmo metodo, permitindo accionar via menu de Acoes nas vistas tree.

d) Passo a passo de utilizacao
------------------------------
1. Abrir um produto qualquer no menu Inventario / Produtos.
2. Clicar no botao "Scan Duplicates" no topo da vista.
   - Em alternativa, na vista de lista de produtos, usar Acoes /
     "Log duplicate barcodes & default codes".
3. Esperar a notificacao com o numero de grupos duplicados encontrados.
4. Abrir os logs do servidor para ver, por barcode/default_code, a lista de
   templates duplicados (ID, display_name e o outro valor associado).

e) Exemplo pratico
------------------
- O cliente executa o scanner e a notificacao indica:
  "Duplicate barcodes: 2 groups | Duplicate default codes: 0 groups."
- No log do servidor aparece:
  `BARCODE DUPLICATE | barcode=5601234567890 | count=3 | templates=[(12, 'Cadeira XPTO', 'CAD-001'), (87, 'Cadeira XPTO COR2', 'CAD-002'), (215, 'Cadeira variante', 'CAD-001-V')]`
- A equipa funcional decide qual produto manter e ajusta os barcodes em massa.

f) FAQ / Resolucao de problemas
-------------------------------
- "Cliquei no botao e nao aparece notificacao":
  Verificar se o utilizador tem permissao no `product.template` e se o servidor
  esta a aceitar `display_notification`. Em qualquer caso o detalhe esta no log
  do servidor.
- "Nao consigo ver o detalhe dos duplicados no UI":
  O modulo escreve em log para evitar criar registos novos (poderiam por si so
  introduzir duplicados de auditoria). A consulta tem de ser no log do servidor.
- "Quero excluir produtos arquivados":
  Hoje o `search` nao filtra por `active`, pelo que produtos arquivados podem
  aparecer. Se for necessario filtrar, ajustar `models/product_template_duplicates.py`.

g) Pontos de atencao
--------------------
- O scan le todos os templates com barcode/default_code preenchidos em memoria;
  em bases com milhoes de produtos pode ser pesado. Para essas dimensoes,
  considerar paginacao ou um SQL direto.
- A notificacao devolvida classifica o sucesso (sem duplicados) com type
  "success" e a presenca de duplicados como type "warning"; nao bloqueia nada.

[FACTO OBSERVADO] o modulo so faz leitura (`sudo().search`) e devolve uma
notificacao; nao escreve nem altera registos.
    """,
    "depends": ["product"],
    "data": [
        "views/product_template_duplicate_scan.xml",
        "data/server_action_duplicate_scan.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
