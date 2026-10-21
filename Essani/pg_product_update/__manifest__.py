# -*- coding: utf-8 -*-

{
    'name': 'PG Atualizacao de Produtos via Google Drive',
    'version': '1.0.24',
    'category': 'Inventory',
    'summary': ('Importa imagens, documentos, categorias e referencias de produtos a partir do Google '
 'Drive.'),
    'description': '''
Objetivo de negocio
===================
Automatiza a atualização do catálogo Essani a partir da estrutura Google Drive: imagens, anexos técnicos, categorias, variantes e referências.

Pre-requisitos
==============
Bibliotecas Google (`google-api-python-client`, `google-auth`, `google-auth-httplib2`) e PIL disponíveis. Parametro `product_update.gdrive_sa_json_b64` com service account em base64. Service account com leitura à Drive. Cron ativo. Estrutura de pastas com `IMAGENS` e pastas documentais esperadas.

Como funciona
=============
Modelo `product.update` usa helper Drive readonly, processa jobs persistentes por cron, cria categorias, imagens e documentos. `product.update.drive.job` guarda progresso. Wizard/planos `pg.product.references.plan` comparam variantes Odoo vs Drive e podem preencher `default_code` em lote. O modelo `pg.documento.orfao.censo` (Vendas > Produtos > Documentos orfaos) encontra os documentos presos a variantes destruidas e separa-os pelo conteudo: os que sao copia exata de um ficheiro ja colocado (redundantes) dos que existem so ali (unicos). A analise so le; religar pela referencia no nome exige aprovacao linha a linha; nada e apagado, arquivado nem substituido.

Passo a passo de utilizacao
===========================
1. Configurar service account e partilha da pasta Drive. 2. Abrir Produtos e acionar atualização/import job. 3. Acompanhar dashboard do job. 4. Para referências, abrir wizard `Pescar referencias`, gerar plano, rever conflitos e aplicar.

Exemplo pratico
===============
Pasta Drive de um produto contém `IMAGENS`, `FICHA TECNICA` e variantes com códigos. O job cria/atualiza imagens do produto, anexa PDFs e o plano sugere preencher `default_code` das variantes sem referência.

FAQ / Resolucao de problemas
============================
Erro Google libraries: instalar dependências no Odoo.sh. Parametro em falta: preencher `product_update.gdrive_sa_json_b64`. Job parado: abrir dashboard e rever `last_error`. Conflitos de referência: resolver duplicados antes de aplicar em modo force.

Pontos de atencao / avisos
==========================
Operação de alto impacto no catálogo. Testar em staging antes de correr em massa. A recuperacao de documentos orfaos corre com `sudo()` de proposito: um orfao nao e legivel por API, porque `ir.attachment` valida o acesso ao registo apontado e esse registo ja nao existe. Por isso nao ha — nem pode haver — um script externo equivalente. O censo classifica pelo `checksum` do conteudo e nao pelo `gdrive_file_id`: contra os dados reais o identificador do Drive apanhou zero casos em 5904, porque o mesmo ficheiro foi carregado varias vezes e recebeu id novo de cada vez, enquanto a comparacao de conteudo apanhou 5388. Religar pela referencia no nome do ficheiro acerta pouco neste catalogo (29 casos, todos ja acessiveis noutro sitio); o valor do censo esta em separar o redundante do unico. Existem caches, commits e locks para lidar com jobs grandes; evitar alterar nomes de pastas esperadas sem ajustar parametros.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['base', 'product', 'website_sale'],
    'data': ['security/pg_references_sync_groups.xml',
 'security/ir.model.access.csv',
 'views/product_update_view.xml',
 'views/product_update_button.xml',
 'views/product_update_job_views.xml',
 'views/pg_product_references_plan_views.xml',
 'views/pg_documento_orfao_views.xml',
 'wizard/pg_product_references_fetch_wizard_views.xml',
 'data/ir_cron.xml',
 'data/ir_config_parameter.xml'],
    'assets': {'web.assets_backend': ['pg_product_update/static/src/js/drive_job_dashboard.js',
                        'pg_product_update/static/src/xml/drive_job_dashboard.xml']},
    'installable': True,
    'application': False,
}
