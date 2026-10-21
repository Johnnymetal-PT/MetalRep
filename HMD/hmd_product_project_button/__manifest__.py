# -*- coding: utf-8 -*-
{
    'name': 'HMD Product Project Button',
    'version': '18.0.1.3.0',
    'summary': 'Botao smart "Projetos" no produto - lista projetos ligados via SO/PO.',
    'description': """
HMD Product Project Button
==========================

a) Objetivo de negocio
----------------------
A HMD trabalha por projeto/encomenda - cada projeto tem `sale.order` e
`purchase.order` associados. Para um responsavel de produto saber em
que projetos um determinado componente esta a ser usado, o standard
nao tem atalho. Este modulo adiciona um botao smart "Projetos" no
produto template e na variante que lista os projetos onde o produto
aparece em alguma linha de venda ou de compra com `project_id`
definido.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `product`, `sale_management`, `purchase`, `project`.
- Os SOs/POs devem ter `project_id` preenchido (campo standard quando
  `sale_project` esta instalado, ou via Studio).

c) Como funciona (tecnico)
--------------------------
1. `product.product._map_product_to_project_ids(product_ids)`
   (`models/product_product.py`):
   - Percorre `sale.order.line` e `purchase.order.line` com produto
     ou template entre os pedidos, agrega `order_id`, le os orders e
     extrai `project_id`. Tem fallback para `product_template_id`
     quando o campo existe.
   - `with_context(active_test=False)`: garante que apanha tambem
     orders arquivados.
   - Tudo em sudo() para evitar problemas de record rules; a logica
     destina-se a contagem read-only.
   - Devolve um defaultdict {product.id: set(project.id)}.

2. Wrappers em `product.template.action_view_related_projects` e
   `product.product.action_view_related_projects`: chamam a acao
   standard `project.open_view_project_all`, restringem `domain` aos
   projetos encontrados e limpam `search_default_*` do contexto.

3. Botões smart com `type="object"`: chamam diretamente
   `action_view_related_projects` no template e na variante. Não há
   indireção por `ir.actions.server` (evita a leitura do campo `code`,
   restrito a `base.group_system`, que partia o botão para utilizadores
   sem esse grupo).

4. View (`views/product_views.xml`): botão smart "Projetos" (ícone
   fa-folder-open) com a contagem; chama `action_view_related_projects`
   no registo atual do formulário (template ou variante).

d) Passo a passo de utilizacao
------------------------------
1. Garantir que `project_id` esta presente nos SOs/POs (depende do
   modulo `sale_project` e/ou Studio na HMD).
2. Instalar `hmd_product_project_button`.
3. Inventario > Artigos > abrir um produto.
4. No topo aparece o botao smart "Projetos" com a contagem.
5. Clicar abre a list de projetos ligados.

e) Exemplo pratico
------------------
Produto "Tecido cima" foi usado em:
  - SO S001 ligado a Projeto P-100;
  - SO S005 ligado a Projeto P-100;
  - PO P099 ligado a Projeto P-205.

`project_usage_count` = 2 (P-100 e P-205, distinct). Clicar abre a
lista com esses dois projetos.

f) FAQ / Resolucao de problemas
-------------------------------
P: O botao mostra 0 mas o produto e usado em projetos. Porque?
R: Os SOs/POs nao tem `project_id` preenchido. O modulo so apanha
   orders com project_id explicito. Validar a config do
   `sale_project` ou Studio.

P: Erro "model project.project not found". O que falta?
R: O modulo `project` nao esta instalado. Instalar antes.

P: Clico no botao e a lista esta vazia mas a contagem era >0.
R: O projeto pode ter sido arquivado entre o compute e o click. O
   compute usa `active_test=False` (deteta arquivados), mas a lista
   final respeita o `active_test` do contexto. Validar.

g) Pontos de atencao / avisos
-----------------------------
- Os botões usam `type="object"` (padrão standard do Odoo). Versões
  anteriores usavam `ir.actions.server` intermédias, removidas em
  18.0.1.1.0 (ver `migrations/`).
- `compute_sudo=True`: o utilizador final ve a contagem mesmo que
  nao tenha leitura aos SOs/POs sensiveis. Importante para nao
  partir o button_box.
- `_logger.info` abundante - util na fase inicial. Em producao,
  considerar baixar para DEBUG.
- A query agregadora tem custo O(linhas SO + linhas PO). Em bases
  grandes, considerar criar indices em
  `sale_order_line.product_id` e `purchase_order_line.product_id`
  (geralmente ja existem).
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['product', 'sale_management', 'purchase', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': False,
}
