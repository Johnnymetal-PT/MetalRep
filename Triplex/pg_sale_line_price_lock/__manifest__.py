# -*- coding: utf-8 -*-
{
    "name": "PG Sale Line Price Lock",
    "version": "17.0.1.0.0",
    "summary": "Põe o preço unitário das linhas de venda em só leitura para um grupo de utilizadores",
    "description": """
PG Sale Line Price Lock
=======================

Objetivo de negócio
-------------------
Alguns utilizadores (ex.: comerciais juniores) devem poder criar/editar encomendas de venda
mas NÃO alterar o preço unitário das linhas. Este módulo torna esse campo só de leitura
para quem pertencer a um grupo de segurança específico.

Pré-requisitos
--------------
- Módulos: `sale_management`.
- Conhecer quais utilizadores devem ficar com preços bloqueados (administrador atribui o grupo).

Como funciona
-------------
- Segurança (security/sale_line_price_security.xml): cria a categoria "Bloqueio de Preços
  de Venda" e o grupo `group_sale_line_price_readonly`.
- `sale.order`: campo calculado `pg_sale_line_prices_readonly` que é True quando o utilizador
  atual pertence a esse grupo.
- Vista (views/sale_order_views.xml): usa esse campo (invisível) para tornar `price_unit`
  readonly nas linhas (tree e form). Na tree mantém também a regra standard de bloqueio
  quando já há quantidade faturada (`qty_invoiced > 0`).

Passo a passo de utilização
---------------------------
1. Instalar o módulo. O `post_init_hook` (hooks.py) atribui logo o grupo aos utilizadores
   listados em `LOCKED_USER_LOGINS` (por login); os que não existirem na BD são ignorados
   com um aviso no log. Para mudar a lista, editar essa constante.
2. Em Definições > Utilizadores e Empresas > Utilizadores, abrir cada utilizador a restringir.
3. Em "Bloqueio de Preços de Venda", ativar o grupo "Linhas de Venda: Preços Só Leitura".
4. Esse utilizador, ao abrir uma encomenda, vê o `price_unit` em só leitura.
5. Os utilizadores SEM o grupo continuam a poder editar o preço unitário normalmente.

Exemplo prático
---------------
A comercial Ana pertence ao grupo; ao abrir o orçamento SO/0001, consegue alterar quantidade
e produto, mas o preço unitário aparece bloqueado (acinzentado). O gestor João, sem o grupo,
edita o preço sem restrições.

FAQ / Resolução de problemas
----------------------------
- P: Adicionei o utilizador ao grupo e continua a poder editar.
  R: Pedir-lhe para recarregar a página/sessão; o campo é computado mas o XPath aplica-se à vista renderizada.
- P: Quero bloquear apenas em alguns estados (ex.: depois de enviado).
  R: Este módulo bloqueia sempre que o utilizador estiver no grupo; uma regra por estado
     exige alterar a vista.
- P: Posso impedir mesmo a alteração por importação/API?
  R: Não — este bloqueio é apenas no UI. Para impedir por API/import é preciso uma regra
     ou um override de write.

Pontos de atenção
-----------------
- O bloqueio é ao nível do UI/vista (readonly); NÃO substitui regras de acesso ao modelo.
- O cálculo do flag é por utilizador (não por encomenda) — todas as ordens de um utilizador
  ficam coerentes na mesma sessão.
""",
    "category": "Sales",
    "author": "Parametro Global",
    "license": "LGPL-3",
    # `pg_product_variant_description_bytesfuel` não é usado por este módulo, mas fornece
    # o campo `product_variant_desc` que a personalização Studio do formulário de venda
    # referencia. Sem esta dependência, o upgrade carrega este módulo primeiro e a
    # validação da vista combinada de `sale.order` falha por o campo ainda não existir.
    "depends": ["sale_management", "pg_product_variant_description_bytesfuel"],
    "data": [
        "security/sale_line_price_security.xml",
        "views/sale_order_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
