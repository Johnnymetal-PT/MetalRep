# -*- coding: utf-8 -*-

{
    'name': 'PG Website Documentos de Produto',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Mostra documentos de produto no website e abre PDFs em nova aba.',
    'description': '''
Objetivo de negocio
===================
Dá ao cliente uma página de produto mais completa, com documentos técnicos, certificados, ficheiros 3D e uma página de categorias própria para a navegação da extranet.

Pre-requisitos
==============
Website/eCommerce instalados. Documentos carregados como `ir.attachment` em `product.template` ou `product.product`. Para filtragem por variante, preencher `variant_ids` no anexo. A categoria pública raiz esperada chama-se `Todas`.

Como funciona
=============
Herda `product.template` para expor anexos do template e das variantes. Herda `ir.attachment` com `variant_ids`. O controller redireciona `/shop` para `/categorias` e renderiza filhos de `Todas`; o JS faz pre-check de acesso e abre o anexo com `download=false`.

Passo a passo de utilizacao
===========================
1. Anexar PDFs ou ficheiros ao produto/variante. 2. Opcionalmente associar o anexo a variantes. 3. Abrir o produto no website e usar o acordeao `Documentos`. 4. Navegar em `/categorias` para ver as famílias visíveis.

Exemplo pratico
===============
Num candeeiro com variantes Preto/Branco, anexar `Ficha Tecnica.pdf` ao template e `Certificado Preto.pdf` à variante Preta. Ao escolher Preto, o certificado específico fica visível; ao clicar no PDF abre em nova aba.

FAQ / Resolucao de problemas
============================
Se o PDF descarrega, confirmar se o link tem a classe `attachment-link` e se o asset frontend foi carregado. Se aparece sem permissao, rever regras de `ir.attachment`. Se `/shop` redireciona de forma inesperada, lembrar que este modulo redefine a entrada principal para `/categorias`.

Pontos de atencao / avisos
==========================
O agrupamento de documentos é por palavras no nome (`FICHA`, `CERTIFICADO`, `3D`). A categoria `Todas` é assumida por nome. Existe JavaScript inline no template de produto; alterações no DOM standard do `website_sale.product` podem exigir ajuste.
''',
    'author': 'Parametro Global SA',
    'depends': ['website_sale', 'base', 'web', 'product'],
    'data': ['security/ir.model.access.csv',
 'security/ir_attachment_access_rights.xml',
 'security/ir_attachment_rules.xml',
 'views/product_template_views.xml',
 'views/website_product_template.xml',
 'views/dynamic_snippet_filter.xml',
 'views/categories_page.xml'],
    'assets': {'web.assets_frontend': ['pg_web_attach_pdf_view/static/src/js/attachment_preview.js',
                         'pg_web_attach_pdf_view/static/src/js/hide_todas.js',
                         'pg_web_attach_pdf_view/static/src/css/styles.css']},
    'installable': True,
    'application': False,
}
