# -*- coding: utf-8 -*-

{
    'name': 'PG Website Shop Redirect - OBSOLETO',
    'version': '1.0',
    'category': 'Website',
    'summary': 'OBSOLETO: redirecionava visitantes anonimos de /shop para login.',
    'description': '''
OBSOLETO
========
Este modulo e legado. Foi criado para bloquear `/shop` a utilizadores nao autenticados.

Substituto
==========
Usar `pg_website_auth_required` para a regra custom da Essani, ou a configuracao standard Odoo 19 em Website/eCommerce (`ecommerce_access = logged_in`) quando bastar bloquear toda a loja.

Nota operacional
================
Nao usar em novas implementacoes. Se ainda estiver instalado numa base, validar rotas `/shop`, `/categorias` e login antes de remover, porque pode coexistir com outros redirects de website.
''',
    'author': 'Parametro Global SA',
    'depends': ['website_sale'],
    'data': ['views/templates.xml'],
    'installable': True,
    'application': False,
}
