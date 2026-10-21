# -*- coding: utf-8 -*-
{
    'name': 'PG Web Attachment PDF View',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Permite abrir os PDFs anexos a um produto numa nova tab do browser em vez de descarregar; agrupa por FICHA TECNICA, CERTIFICADO, 3D, OUTROS.',
    'author': 'Parametro Global SA',
    'depends': ['website_sale'],
    'data': [
        'views/product_template_views.xml',
        'views/website_product_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_attach_pdf_view/static/src/js/attachment_preview.js',
        ],
    },
    'description': """
PG Web Attach PDF View
======================

a) Objetivo de negocio
----------------------
Mostrar na pagina publica do produto os documentos tecnicos
disponiveis (ficha tecnica, certificado, 3D, outros) e abri-los em
nova tab em vez de forcar download. Reduz friccao do cliente que so
quer consultar.

b) Pre-requisitos
-----------------
- Modulo standard ``website_sale``.
- Anexos (``ir.attachment``) ligados ao ``product.template`` (campo
  ``res_model='product.template'`` e ``res_id`` apontando para o
  produto).
- Convencao de nomes nos anexos: o titulo do anexo determina o grupo
  (ver "Como funciona").

c) Como funciona
----------------
- Override de ``product.template`` em ``models/product_template.py``:
  - ``attachment_ids`` (One2many ir.attachment) - lista de documentos
    ligados ao produto.
  - ``_get_document_groups()``: agrupa anexos por palavra-chave no
    nome:
    - contem "3D" -> grupo "3D"
    - contem "CERTIFICADO" -> "CERTIFICADO DE CONFORMIDADE"
    - contem "FICHA" -> "FICHA TECNICA"
    - caso contrario -> "OUTROS"
    *Match case-sensitive - manter o convencionado em maiusculas.*
  - ``_get_attachment_description(attachment_id)``: helper para QWeb
    obter a descricao do anexo.
- ``views/website_product_template.xml`` injeta na pagina publica do
  produto os blocos com os grupos.
- ``views/product_template_views.xml`` no backoffice mostra o campo
  ``attachment_ids`` para facilitar a gestao dos documentos.
- JS frontend ``pg_attach_pdf_view/static/src/js/attachment_preview.js``
  intercepta o clique no link do PDF e abre ``window.open()`` em nova
  tab em vez de download.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. No backoffice abrir o produto e ir aos anexos.
3. Carregar PDFs com nomes seguindo a convencao:
   - ``FICHA TECNICA - <produto>.pdf``
   - ``CERTIFICADO DE CONFORMIDADE - <produto>.pdf``
   - ``3D - <produto>.pdf`` ou ``<produto> 3D.pdf``
   - Outros nomes caem no grupo "OUTROS".
4. Pagina publica do produto mostra agora os documentos por grupo,
   cada um abre em nova tab.

e) Exemplo pratico
------------------
Produto "Cadeira X" tem 3 anexos:
- ``FICHA TECNICA - Cadeira X.pdf``
- ``CERTIFICADO DE CONFORMIDADE.pdf``
- ``Manual de Montagem.pdf``
Na pagina publica aparecem 3 seccoes: "FICHA TECNICA" (1 link),
"CERTIFICADO DE CONFORMIDADE" (1 link), "OUTROS" (1 link). Clicar
em qualquer um abre em nova tab.

f) FAQ / Resolucao de problemas
-------------------------------
- *"PDF aparece no grupo OUTROS"* -> nome do anexo nao contem
  nenhuma palavra-chave (case sensitive). Renomear para incluir
  "FICHA", "CERTIFICADO" ou "3D" conforme aplicavel.
- *"PDF ainda descarrega em vez de abrir"* -> JS nao carregou.
  Recarregar /web/refresh; verificar o caminho do asset
  ``pg_attach_pdf_view/static/src/js/attachment_preview.js``.

g) Pontos de atencao / avisos
-----------------------------
- O agrupamento e por palavra-chave **maiuscula**; "ficha tecnica"
  em minusculas cai em "OUTROS". A convencao tem de ser respeitada
  na carga dos anexos.
- O dominio do ``One2many`` so filtra por ``res_model =
  'product.template'`` - se houver anexos ligados a
  ``product.product`` em vez de ``product.template``, nao aparecem.
- O JS frontend assume estrutura HTML especifica do template - se a
  view for alterada, validar se o seletor continua a funcionar.
""",
    'installable': True,
    'application': False,
}
