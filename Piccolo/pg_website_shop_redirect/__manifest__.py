# -*- coding: utf-8 -*-
# __manifest__.py
{
    'name': 'PG Website Shop Redirect',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Bloqueia /shop a utilizadores nao autenticados e redireciona para /web/login.',
    'author': 'Parametro Global',
    'depends': ['website_sale'],
    'data': [
        'views/templates.xml',
    ],
    'description': """
PG Website Shop Redirect
========================

a) Objetivo de negocio
----------------------
A loja /shop da Piccolo so e visivel a clientes autenticados
(precos B2B, catalogo restrito). Este modulo impede que visitantes
anonimos vejam /shop e empurra-os para o ecra de login.

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale``.
- Pagina /web/login standard ativa.

c) Como funciona
----------------
- ``controllers/main.py`` define ``WebsiteShopRedirect`` que
  **substitui** a rota ``/shop`` do core:
  - Se ``request.env.user._is_public()`` -> redirect ``/web/login``.
  - Caso contrario, delega no ``WebsiteSale().shop()`` original.
- ``views/templates.xml`` contem ajustes visuais auxiliares
  (mensagens, oculta CTAs publicas).

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Em sessao anonima, abrir /shop - aterra em /web/login.
3. Apos login, /shop funciona normal.

e) Exemplo pratico
------------------
Visitante carrega link partilhado por email para ``/shop/product/123``
sem estar autenticado: e redirecionado para /web/login com o
``redirect=`` no URL para regressar a pagina apos autenticar
(comportamento standard do /web/login).

f) FAQ / Resolucao de problemas
-------------------------------
- *"Continuo a ver /shop sem login"* -> outra customizacao pode estar
  a sobrepor o controller. Validar com ``odoo --log-level=debug`` que
  o ``WebsiteShopRedirect.shop_redirect`` esta a ser chamado.
- *"Quero redirecionar para a home em vez de login"* -> existe linha
  comentada ``# return request.redirect('/')`` no controller.

g) Pontos de atencao / avisos
-----------------------------
- Combina com ``pg_hide_prices`` (que ja esconde precos a
  publicos). Sem este redirect, anonimos veem a loja sem precos;
  com este, nem chegam a ver a loja.
- A rota substitui a do ``website_sale`` - se outro modulo tambem
  herdar ``/shop``, a ordem de carregamento determina quem ganha
  (gerir via ``depends`` do manifest).
""",
    'installable': True,
    'application': False,
}
