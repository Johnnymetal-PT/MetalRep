# -*- coding: utf-8 -*-

{
    'name': 'PG Modelos 3D em Produtos',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Adiciona ficheiros 3D a produtos e variantes.',
    'description': '''
Objetivo de negocio
===================
Permite associar modelos 3D a artigos para uso interno e para apresentação no eCommerce.

Pre-requisitos
==============
Modulo `pg_3d_viewer` instalado. Ficheiros preferenciais `.glb` ou `.gltf`; `.fbx` e `.dxf` podem ser guardados mas não têm preview web pelo model-viewer.

Como funciona
=============
Herda `product.template` e `product.product`. O template guarda o modelo base; a variante pode herdar esse modelo ou substituir por um ficheiro específico. Campo boolean calcula se o ficheiro é previewable.

Passo a passo de utilizacao
===========================
1. Abrir Produto > separador 3D. 2. Carregar ficheiro `.glb`/`.gltf`. 3. Guardar. 4. Se houver variantes com modelo próprio, editar a variante e carregar ficheiro específico.

Exemplo pratico
===============
Produto `Cadeira A` recebe `cadeira.glb` no template. A variante `Cadeira A / Preto` pode usar o mesmo ficheiro ou receber `cadeira_preta.glb`.

FAQ / Resolucao de problemas
============================
Sem preview: confirmar extensão `.glb`/`.gltf`. Se o ficheiro é grande, testar carregamento no browser. Se a variante mostra o modelo errado, verificar se existe ficheiro no campo de variante.

Pontos de atencao / avisos
==========================
Baseado em OCA e adaptado ao prefixo PG. A renderização depende do widget `model_viewer` e da biblioteca frontend fornecida por `pg_3d_viewer`.
''',
    'author': 'TAKOBI, Openindustry.it, Odoo Community Association (OCA), adaptado PG',
    'website': 'https://github.com/OCA/product-attribute',
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': ['eLBati'],
    'depends': ['pg_3d_viewer', 'product'],
    'data': ['views/product_views.xml'],
    'demo': ['data/product_demo.xml'],
    'installable': True,
    'application': False,
}
