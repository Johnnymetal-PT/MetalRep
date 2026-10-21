# -*- coding: utf-8 -*-
{
    'name': 'PG Shop Page Public Override',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Mantem /shop acessivel a utilizadores publicos e disponibiliza /artigos + /smart-shop.',
    'description': """
PG Shop Page Public Override (HMD)
==================================

a) Objetivo de negocio
----------------------
No fluxo standard do Odoo `website_sale`, a pagina `/shop` pode redirecionar
para login quando o utilizador publico nao tem direito a ver determinados
produtos/pricelists (depende da configuracao Public Pricelist + Public
Category). Para a HMD interessa que o publico veja sempre o catalogo sem
ter de iniciar sessao. Este modulo:
  - garante que `/shop` esta sempre acessivel a publico (redireciona para
    a paginacao 1, mantendo o fluxo);
  - publica uma rota alternativa `/artigos` que pagina manualmente
    `product.template` publicados, util para um catalogo simplificado
    (sem variantes/carrinho complexo);
  - publica `/smart-shop` que decide automaticamente o destino conforme
    o utilizador (publico -> `/artigos`, autenticado -> `/shop`).

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo standard `website_sale` instalado (loja online).
- Template QWeb `website.artigos` definido (entregue via Studio ou via
  outro modulo do projeto). Sem este template, `/artigos` devolve erro
  ao renderizar - ver FAQ.
- Produtos publicados (`website_published = True`) para aparecerem em
  `/artigos`.

c) Como funciona (tecnico)
--------------------------
Tres controllers HTTP, todos em `controllers/main.py`:
1. `ShopPublicAccess.public_shop` - rota `/shop` com `auth='public'`. O
   override forca uma 302 para `/shop/page/1` para evitar qualquer
   redirect para login que o controller standard faca quando o publico
   nao consegue resolver o pricelist.
2. `WebsiteArtigosController.artigos_page` - rota custom `/artigos` (com
   paginacao `/artigos/page/<int:page>`). Pesquisa direta a
   `product.template` com `website_published=True` em `sudo()` para
   ignorar record rules do publico, e usa `request.website.pager` (NAO
   `Website.pager`) para construir o pager - chamada equivalente, mas a
   versao via `request.website` e a que o framework garante estar
   disponivel em qualquer contexto de website.
3. `ShopRedirectController.smart_shop_redirect` - rota `/smart-shop` que
   olha para `request.env.user` e decide:
     - publico -> redireciona para `/artigos` (catalogo simplificado);
     - autenticado -> redireciona para `/shop` (loja standard).
   Permite por links externos do website (newsletter, qr code) usarem
   uma URL unica que se adapta a quem clica.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_shop_public_override` na BD HMD.
2. Confirmar que existem produtos com `website_published = True`.
3. Garantir que o template QWeb `website.artigos` esta criado (em
   Studio ou via XML; precisa de iterar a variavel `products` e
   renderizar o `pager`).
4. Em vez de linkar `/shop` diretamente em emails/newsletters/QR,
   apontar para `/smart-shop` para que utilizadores publicos sigam o
   catalogo simplificado.

e) Exemplo pratico
------------------
Utilizador publico clica num QR code que aponta para
`https://hmd.pt/smart-shop`:
  - `smart_shop_redirect` deteta `user._is_public()` -> 302 para
    `/artigos`.
  - `artigos_page` corre com `page=1`, pesquisa os primeiros 20
    `product.template` publicados, monta o pager (5 paginas visiveis ao
    redor da atual) e renderiza `website.artigos`.
  - O publico ve o catalogo sem ter sido forcado a iniciar sessao.

Utilizador autenticado clica no mesmo link:
  - `smart_shop_redirect` -> 302 para `/shop`.
  - `public_shop` override garante 302 para `/shop/page/1` (evita o
    redirect para login que o standard poderia disparar).

f) FAQ / Resolucao de problemas
-------------------------------
P: `/artigos` devolve "QWebException: External ID not found in the
   system: website.artigos". O que fazer?
R: O template QWeb `website.artigos` nao existe. Criar o template via
   Studio (Website > Pages) ou via XML noutro modulo. Tem de iterar
   `products` e renderizar `pager`.

P: `/shop` continua a redirecionar para login. Porque?
R: O override aplica-se apenas a `/shop` sem subpath. Se o redirect
   ocorre noutra rota (ex.: `/shop/category/...`), e necessario
   override adicional. Validar tambem que o publico tem pricelist
   default acessivel.

P: O publico esta a ver produtos que nao deveria. Porque?
R: `artigos_page` usa `sudo()` por design (para nao bloquear o publico
   nem por record rules nem por ACL). Filtra apenas por
   `website_published=True`. Se for preciso restringir mais, ajustar o
   `domain` em `controllers/main.py`.

P: `request.website.pager` falha. Posso usar `Website().pager`?
R: Nao. O metodo de instancia em `Website` precisa de contexto de
   request/website resolvido. Manter `request.website.pager` como esta.

g) Pontos de atencao / avisos
-----------------------------
- O override `/shop` substitui a rota standard do `website_sale`. Em
  upgrade, se o controller standard for refatorado, validar que o
  comportamento ainda e o esperado.
- `sudo()` em `artigos_page` ignora ACL/record rules de
  `product.template`. Se o cliente decidir esconder produtos por
  empresa/segmento, este controller nao respeita essa decisao - exige
  evolucao.
- Nao usa template no manifest (`data` vazio): toda a logica esta em
  Python e o template `website.artigos` e externo a este modulo.
""",
    'depends': ['website_sale'],
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'category': 'Website',
    'installable': True,
    'application': False,
}
