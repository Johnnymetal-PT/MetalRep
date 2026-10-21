# -*- coding: utf-8 -*-
# __manifest__.py
{
    'name': 'PG Website Order Bypass',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Confirma a Sale Order do checkout sem exigir pagamento online; cria fatura quando a politica e "order" e envia email de confirmacao.',
    'author': 'Parametro Global',
    'depends': ['website_sale', 'sale', 'account'],
    'data': [
        'views/payment_acquirer.xml',
        'views/templates.xml',
    ],
    'description': """
PG Website Order Bypass
=======================

a) Objetivo de negocio
----------------------
A Piccolo nao cobra online - o checkout do website serve apenas para
o cliente colocar a encomenda. Este modulo curto-circuita o passo de
pagamento e confirma a SO imediatamente, dispara fatura (quando a
politica de faturacao e "ao confirmar") e envia o email de
confirmacao standard.

b) Pre-requisitos
-----------------
- Modulos standard ``website_sale``, ``sale``, ``account``.
- Template de email ``sale.email_template_edi_sale`` (vem com o
  ``sale``).
- Politica de faturacao do produto definida (``order`` para faturar
  ja, ``delivery`` para faturar so depois da entrega).

c) Como funciona
----------------
- Override do controller ``WebsiteSale`` em ``controllers/main.py``:
  - Rota ``/shop/confirm_order`` (substitui a do core):
    1. Procura o carrinho atual com ``request.website.sale_get_order()``.
    2. Sem carrinho -> redirect /shop.
    3. ``order.action_confirm()`` (confirma a SO).
    4. Se a politica de faturacao for ``order``, cria fatura com
       ``order._create_invoices()``.
    5. Envia email com o template ``sale.email_template_edi_sale``
       em modo ``sudo`` (para utilizadores publicos).
    6. Redirect para ``/shop/confirmation``.
- ``views/payment_acquirer.xml`` e ``views/templates.xml``: ajustes
  visuais na pagina de pagamento para esconder providers e textos
  irrelevantes neste fluxo.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Cliente coloca produtos no carrinho.
3. Faz checkout, preenche moradas.
4. Em vez de ecra de pagamento, salta direto para "Realizar
   Encomenda" e e redirecionado para a pagina de confirmacao com
   email enviado.

e) Exemplo pratico
------------------
Cliente "Hotel XYZ" confirma carrinho com 3 cadeiras. SO ``S00210``
fica em estado "sale" automaticamente, fatura ``INV/2026/0058`` e
criada (politica = ``order``) e o cliente recebe email "Encomenda
confirmada".

f) FAQ / Resolucao de problemas
-------------------------------
- *"Encomenda confirmada mas sem fatura"* -> politica de faturacao
  do produto e ``delivery``; faturacao so acontece apos pickings.
- *"Cliente nao recebeu email"* -> verificar mail server e que o
  template ``sale.email_template_edi_sale`` nao foi
  removido/desativado.
- *"Pagamentos online voltaram a aparecer"* -> outra customizacao
  pode ter sobreposto o template ``views/templates.xml`` ou
  ``views/payment_acquirer.xml`` deste modulo.

g) Pontos de atencao / avisos
-----------------------------
- A confirmacao corre como utilizador publico via ``sudo()`` no envio
  de mail - validar que regras de seguranca permitem; em ambientes
  com sudo restrito pode ter de ser revisto.
- Nao ha verificacao de stock antes de confirmar. Em fluxo MTO da
  Piccolo nao e problema (a producao arranca depois); para MTS
  significa que clientes podem encomendar mais do que ha em stock.
- Casa com ``pg_paynow_button`` (que renomeia o botao para
  "Realizar Encomenda") - manter os dois alinhados.
""",
    'installable': True,
    'application': False,
}
