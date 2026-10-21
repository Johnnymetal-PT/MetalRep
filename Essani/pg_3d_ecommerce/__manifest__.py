# -*- coding: utf-8 -*-

{
    'name': 'PG eCommerce Visualizador 3D',
    'version': '19.0.2.0.0',
    'category': 'Website',
    'summary': 'Mostra modelos 3D dos produtos na pagina de eCommerce.',
    'description': '''
Objetivo de negocio
===================
Permite ao cliente visualizar artigos em 3D diretamente na página de produto, útil para catálogo técnico e produtos onde forma/volume importam.

Pre-requisitos
==============
Modelos 3D carregados através de `pg_product_model_viewer`. Ficheiros `.glb` ou `.gltf` para preview. Website/eCommerce instalado.

Como funciona
=============
Herda o template `website_sale.product`, adiciona botão e modal com `<model-viewer>`. JS move modais para o `body` para evitar problemas de z-index e gere fullscreen.

Passo a passo de utilizacao
===========================
1. Carregar modelo 3D no produto. 2. Publicar produto no website. 3. Abrir página de produto. 4. Clicar em `Visualizador 3D`.

Exemplo pratico
===============
Produto `Sofá Modular` com `sofa.glb` mostra botão 3D; o cliente abre o modal e roda o modelo com o rato.

FAQ / Resolucao de problemas
============================
Se o botão não aparece, confirmar campo `gltf_3d_model` e extensão. Se modal fica atrás da página, verificar CSS/z-index e se o JS foi carregado. Se o modelo não carrega, testar URL `/web/content/product.template/<id>/gltf_3d_model`.

Pontos de atencao / avisos
==========================
Renderização depende de suporte browser a Web Components/model-viewer. Ficheiros grandes impactam performance do produto.
''',
    'author': 'TAKOBI, Openindustry.it, Odoo Community Association (OCA), adaptado PG',
    'website': 'https://github.com/OCA/e-commerce',
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': ['eLBati'],
    'depends': ['pg_product_model_viewer', 'website_sale'],
    'data': ['views/frontend_templates.xml'],
    'assets': {'web.assets_frontend': ['pg_3d_ecommerce/static/src/js/product_model_viewer.js',
                         'pg_3d_ecommerce/static/src/scss/product_model_viewer.scss']},
    'installable': True,
    'application': False,
}
