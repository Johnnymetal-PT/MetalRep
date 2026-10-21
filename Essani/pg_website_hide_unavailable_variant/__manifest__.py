# -*- coding: utf-8 -*-

{
    'name': 'PG Ocultar Variantes Indisponiveis',
    'version': '1.2',
    'category': 'eCommerce',
    'summary': 'Oculta no website valores de atributos que levariam a variantes escondidas.',
    'description': '''
Objetivo de negocio
===================
Evita que o cliente selecione combinações de variantes que não devem estar disponíveis no website.

Pre-requisitos
==============
Website Sale Stock instalado. Campo `hide_on_website` preenchido nas variantes a esconder. Atributos podem definir `unavailable_value_view_type`.

Como funciona
=============
Herda `product.template` para filtrar combinações quando o contexto `special_call` está ativo. Controller JSON devolve combinações válidas. Patch JS do `WebsiteSale` esconde options/radios/pills inválidos, corrige seleção e adiciona histórico anterior/limpar.

Passo a passo de utilizacao
===========================
1. Abrir variante de produto. 2. Ativar `hide_on_website`. 3. Abrir produto no website. 4. Confirmar que valores que levam à variante escondida deixam de aparecer.

Exemplo pratico
===============
Produto com Cor Preto/Branco e Tamanho S/M tem variante Preto M marcada `hide_on_website`. Ao escolher Preto, o tamanho M desaparece ou deixa de ser selecionável.

FAQ / Resolucao de problemas
============================
Se valor ainda aparece, confirmar se a variante exata está marcada e se o asset `hide.js` carregou. Se a seleção salta para outro valor, é esperado quando a opção atual fica inválida. Se os botões não aparecem, rever template `website_sale.variants` em Odoo 19.

Pontos de atencao / avisos
==========================
Override sensível a alterações do configurador de variantes. O controller é público mas só devolve IDs de combinações, não preços/dados sensíveis.
''',
    'author': 'ErpMstar Solutions, adaptado PG',
    'depends': ['website_sale_stock'],
    'data': ['views/views.xml', 'views/templates.xml'],
    'assets': {'web.assets_frontend': ['pg_website_hide_unavailable_variant/static/src/js/hide.js']},
    'images': ['static/description/banner.gif'],
    'price': 40,
    'currency': 'EUR',
    'installable': True,
    'application': True,
}
