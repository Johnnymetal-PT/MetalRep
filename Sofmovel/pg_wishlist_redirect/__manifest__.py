{
    'name': 'PG Wishlist No Redirection Fix',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Website',
    'summary': 'Pagina /custom/wishlist que nao redireciona para /shop quando a wishlist esta vazia.',
    'description': """
PG Wishlist No Redirection Fix
==============================

a) Objetivo de negocio
----------------------
O comportamento standard do `website_sale_wishlist` redireciona o utilizador
para `/shop` quando a wishlist esta vazia. Para o caso de uso do projeto, a
equipa precisa que o utilizador continue na pagina da wishlist (mesmo sem
itens) com a mensagem "A sua wishlist esta vazia.". Este modulo introduz uma
rota paralela `/custom/wishlist` que renderiza sempre a vista, com lista
vazia se for o caso.

b) Pre-requisitos
-----------------
- Modulo standard `website_sale_wishlist` instalado.
- Acesso ao website (route com `auth='public'`, mas internamente exige
  utilizador autenticado: se nao houver `partner`, redireciona para
  `/web/login`).

c) Como funciona
----------------
- `controllers/wishlist_controller.py` define `CustomWishlistController`:
  - Rota `/custom/wishlist`, `type='http'`, `auth='public'`, `website=True`.
  - Vai buscar `request.env.user.partner_id`; se nao houver, redireciona
    para `/web/login`.
  - Pesquisa `product.wishlist` para esse parceiro (sudo) e renderiza o
    template standard `website_sale_wishlist.product_wishlist` com:
    - `wishes` = recordset (pode estar vazio)
    - `empty_message` = "Your wishlist is currently empty."

d) Passo a passo de utilizacao
------------------------------
1. Apos instalar o modulo, atualizar links/menus do website para apontar
   para `/custom/wishlist` em vez de `/shop/wishlist`.
2. Validar:
   - Utilizador autenticado com wishlist nao vazia -> ve a lista.
   - Utilizador autenticado com wishlist vazia -> ve a pagina com mensagem
     em vez de ser redirecionado.

e) Exemplo pratico
------------------
- Cliente entra em `/custom/wishlist`:
  - Se ja adicionou produtos: ve-os no template normal.
  - Se nao adicionou: ve a pagina (sem redirect para `/shop`) com a
    mensagem da wishlist vazia.

f) FAQ / Resolucao de problemas
-------------------------------
- "Continuo a ser redirecionado para /shop":
  Confirmar que o link onde clicou aponta para `/custom/wishlist`. A rota
  standard `/shop/wishlist` continua a ter o comportamento original.
- "Pagina mostra mensagem em ingles":
  A `empty_message` esta hardcoded em ingles. Para localizar, editar o
  controller ou usar um template proprio com `_("...")`.

g) Pontos de atencao
--------------------
- A `empty_message` esta em ingles ("Your wishlist is currently empty."). Para
  Sofmovel deve ser PT - ponto a melhorar.
- A rota e publica mas requer parceiro; utilizadores anonimos sao mandados
  para `/web/login`.
- Reutiliza o template `website_sale_wishlist.product_wishlist`: se esse
  template mudar de variaveis em versoes futuras, a renderizacao parte.

[FACTO OBSERVADO] o modulo nao altera a rota original; introduz uma
adicional. Logo, links antigos para `/shop/wishlist` continuam com o
comportamento standard.
    """,
    'depends': ['website_sale_wishlist'],
    'data': [],
    'installable': True,
    'application': False,
}
