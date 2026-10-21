# -*- coding: utf-8 -*-

{
    'name': 'PG Widget Model Viewer',
    'version': '19.0.2.0.0',
    'category': 'Web',
    'summary': 'Widget backend para visualizar ficheiros 3D em campos binarios.',
    'description': '''
Objetivo de negocio
===================
Dá aos utilizadores de backoffice preview visual de modelos 3D sem descarregar ficheiros.

Pre-requisitos
==============
Modulo Web instalado. Biblioteca `model-viewer.min.js` carregada pelos assets. Ficheiros `.glb`/`.gltf` para preview; outros formatos são guardados mas mostram aviso.

Como funciona
=============
Regista um field widget `model_viewer` baseado no `BinaryField`. Se o binário está guardado como attachment, constrói URL `/web/content`; se está em memória, usa data URI. O template OWL injeta `<model-viewer>` e botão fullscreen.

Passo a passo de utilizacao
===========================
1. Usar `widget="model_viewer"` num campo binário. 2. Definir atributo `filename` para o campo com nome do ficheiro. 3. Carregar modelo. 4. Usar preview/fullscreen.

Exemplo pratico
===============
O modulo `pg_product_model_viewer` usa este widget no separador 3D de produtos.

FAQ / Resolucao de problemas
============================
Se mostra aviso de formato, converter para `.glb`/`.gltf`. Se o widget não existe, limpar assets e confirmar dependência. Se o ficheiro não abre, validar permissões do `/web/content`.

Pontos de atencao / avisos
==========================
Base de origem OCA. Alterações devem manter compatibilidade com OWL/BinaryField do Odoo 19.
''',
    'author': 'TAKOBI, Openindustry.it, Odoo Community Association (OCA), adaptado PG',
    'website': 'https://github.com/OCA/web',
    'license': 'AGPL-3',
    'development_status': 'Beta',
    'maintainers': ['eLBati'],
    'depends': ['web'],
    'data': ['views/assets.xml'],
    'assets': {'web.assets_backend': ['pg_3d_viewer/static/src/js/web_widget_model_viewer.js',
                        'pg_3d_viewer/static/src/xml/web_widget_model_viewer.xml']},
    'installable': True,
    'application': False,
}
