# -*- coding: utf-8 -*-

{
    'name': 'PG Website Product Visibility',
    'version': '1.0',
    'category': 'eCommerce',
    'summary': 'Filtra produtos visiveis no website por visitante ou cliente.',
    'description': '''
Objetivo de negocio
===================
Permite que cada cliente/visitante veja apenas o catálogo que lhe está autorizado, suportando extranet comercial com acesso segmentado.

Pre-requisitos
==============
Website/eCommerce instalado. Ativar opção `Is product visibility` nas definições Website. Configurar produtos, categorias ou variantes permitidas em visitantes e contactos.

Como funciona
=============
Adiciona many2many em `res.partner`, `res.company`, `website` e `res.config.settings`. Herda `website.sale_product_domain()` para devolver domínio restrito e marca flags auxiliares `product_attr_active`/`attr_active` para templates de variantes.

Passo a passo de utilizacao
===========================
1. Ativar visibilidade nas definições. 2. Definir produtos/categorias/variantes para visitantes. 3. Definir permissões no contacto para clientes autenticados. 4. Testar loja como visitante e como portal.

Exemplo pratico
===============
Visitante só tem categoria `Destaques`; cliente `Empresa A` tem categorias `Cadeiras` e `Mesas`. Cada um vê apenas os produtos dessas categorias.

FAQ / Resolucao de problemas
============================
Se a loja fica vazia, confirmar se há produtos/categorias atribuídos. Se variantes não aparecem, validar `product_variant_ids`. Se performance degradar, rever volume: o domínio recalcula flags com `sudo()`.

Pontos de atencao / avisos
==========================
Addon externo adaptado. O método `sale_product_domain()` escreve flags em massa durante pedidos website, o que é um efeito lateral importante para performance e concorrência. Alterar com cautela.
''',
    'author': 'BROWSEINFO, adaptado Parametro Global',
    'website': 'https://www.browseinfo.com/demo-request?app=website_product_visibility&version=18&edition=Community',
    'license': 'OPL-1',
    'depends': ['base', 'sale_management', 'website_sale'],
    'data': ['security/ir.model.access.csv',
 'views/res_partner_view.xml',
 'views/product_visibility_template.xml'],
    'images': ['static/description/Banner.gif'],
    'price': 15,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
    'live_test_url': 'https://www.browseinfo.com/demo-request?app=website_product_visibility&version=18&edition=Community',
}
