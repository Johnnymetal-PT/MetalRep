# -*- coding: utf-8 -*-
{
    'name': 'PG Multi Attachment Access',
    'version': '17.0.1.0.0',
    'category': 'Technical',
    'summary': 'Leitura dos anexos das linhas (Product Multi Attachment) a quem pode ler a linha, '
               'mesmo quando o anexo pertence a outra empresa (intercompany).',
    'description': """
PG Multi Attachment Access
==========================

Problema de negócio
-------------------
O módulo `pg_product_multi_attachment` mostra, nas linhas de venda/compra e no produto, um campo
`attachment_ids` (widget many2many_binary) com os documentos/imagens do produto. Em cenário
intercompany, `pg_intercompany_po_so_sync` copia esses anexos das linhas de **compra de uma
empresa** (ex.: Triplex Interiores) para as linhas de **venda de outra empresa** (ex.: Oficinna 22),
mas o anexo mantém-se "filho" da `purchase.order.line` de origem (`res_model=purchase.order.line`).

O `ir.attachment` do Odoo autoriza a leitura de um anexo com base no acesso ao **registo-pai**.
Como a linha de compra pertence a outra empresa, um utilizador que só tem essa outra empresa
(ex.: um utilizador de Produção da Oficinna 22) **não** consegue ler o anexo — recebe
"Erro de Acesso: Anexo (ir.attachment)" ao abrir/consultar a linha de venda, apesar de poder
ler a própria linha de venda.

O que este módulo faz
--------------------
Estende `ir.attachment` (`_search` + `check`) para, **apenas em leitura**, autorizar um anexo
quando este é referenciado pelo campo `attachment_ids` de um registo que o utilizador **consegue
mesmo ler** (sale.order.line / purchase.order.line / product.product / product.template).

Segurança
---------
- As pesquisas de referência correm com os **direitos do próprio utilizador**: um registo que o
  utilizador não pode ver (ex.: a linha de compra da outra empresa) **nunca** concede acesso.
  Assim, o utilizador vê o documento **através da sua linha de venda**, sem qualquer acesso aos
  registos da outra empresa.
- Só alarga **leitura**. Escrita/criação/eliminação mantêm o comportamento standard.
- O alargamento no `_search` só se aplica quando a pesquisa é dirigida a ids concretos
  (`('id', 'in', ...)`), que é o caso do widget many2many_binary — não altera pesquisas amplas.
- Reversível: desinstalar o módulo repõe o comportamento standard.

Dependências
------------
- `pg_product_multi_attachment` (define o campo `attachment_ids`).

Notas
-----
- Módulo separado (não altera o `pg_product_multi_attachment` de terceiros).
- `auto_install=True`: instala-se automaticamente onde o `pg_product_multi_attachment` existir.
""",
    'author': 'Parâmetro Global',
    'website': 'https://parametro.global',
    'depends': ['pg_product_multi_attachment'],
    'data': [],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
    'application': False,
}
