{
    'name': 'PG Web Attachment PDF View',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Documentos PDF do produto no website (abrir em vez de descarregar) + ajustes aos snippets dinâmicos',
    'description': """
PG Web Attachment PDF View
==========================

Este módulo junta duas funcionalidades relacionadas com o website de produto:
1) abrir documentos PDF do produto em vez de os descarregar; 2) ajustes aos snippets
dinâmicos (limite, dedupe, render direto de templates).

Objetivo de negócio
-------------------
- Apresentar no website os documentos do produto (fichas técnicas, certificados, 3D) por
  categoria, com pré-visualização no browser.
- Permitir mostrar mais produtos nos snippets dinâmicos (até 500) e evitar duplicados/produto
  atual.

Pré-requisitos
--------------
- Módulos: `website_sale`, `base`, `web`, `product`.
- Documentos do produto carregados em `ir.attachment` com `res_model=product.template` e
  `res_id` do produto.
- Para o agrupamento por categoria, os nomes dos ficheiros devem conter as palavras-chave:
  "FICHA", "CERTIFICADO", "3D" (caso contrário caem em "OUTROS").

Como funciona
-------------
1) Documentos do produto na página web
- `product.template`: adiciona `attachment_ids` (One2many para ir.attachment do próprio
  produto) e o helper `_get_document_groups()` que agrupa os documentos por tipo a partir
  do NOME do ficheiro: "FICHA TÉCNICA", "CERTIFICADO DE CONFORMIDADE", "3D" e "OUTROS".
- Frontend (attachment_preview.js): abre os PDFs num novo separador em vez de os descarregar.
- Segurança (security/*.xml + csv): regras de acesso aos anexos no contexto do website.

2) Limite e normalização dos snippets dinâmicos de produto
Estende `website.snippet.filter`:
- Eleva o limite máximo de registos (cap = 500) — `_check_limit`.
- Em `_prepare_values`, vai buscar os produtos (por ir.filters ou ir.actions.server), remove
  duplicados ao nível do template e salta o produto atual (`_dedupe_to_templates`).
- Snippets "Alternative/Related" mantêm `product.template` (sem converter para variantes);
  restantes são convertidos para variante.
- Resolve a lista de preços ativa sem usar `website.get_current_pricelist()` (método ausente
  neste build) — ver `_get_active_pricelist`.
- `_filter_records_to_values` sabe renderizar templates diretamente (preço via
  `_get_combination_info` ou fallback para pricelist/`list_price`).

Passo a passo de utilização
---------------------------
1. No produto (backend), carregar os documentos com nomes que incluam as palavras-chave
   (ex.: "FICHA TECNICA Sofá X.pdf").
2. Publicar o produto; na página web aparecem as secções "FICHA TÉCNICA", "CERTIFICADO DE
   CONFORMIDADE", "3D" e "OUTROS" com os ficheiros agrupados.
3. Para os snippets dinâmicos: editar um snippet de produtos no website, ajustar o limite
   até 500 e (re)carregar — os duplicados ficam removidos e o produto atual escondido.

Exemplo prático
---------------
Produto "Sofá X" com 3 anexos: "FICHA TECNICA Sofá X.pdf", "CERTIFICADO ISO.pdf",
"Sofá X 3D.glb". A página web mostra três secções com os respetivos ficheiros, abrindo o PDF
em separador novo. Um snippet "Related products" mostra até 500 produtos relacionados.

FAQ / Resolução de problemas
----------------------------
- P: O JS de abrir em separador não funciona.
  R: O caminho do asset aponta para `pg_attach_pdf_view/...` (sem `web_`); corrigir o
     prefixo para `pg_web_attach_pdf_view/...` no manifesto (ver Pontos de atenção).
- P: Um documento foi para "OUTROS".
  R: O nome do ficheiro não contém nenhuma das palavras-chave (FICHA/CERTIFICADO/3D).
- P: O snippet só mostra 16 produtos.
  R: Aumentar o limite do snippet (cap suportado = 500). Se o limite acima de 500 der erro,
     é por validação intencional.
- P: Aparece o produto atual no "Related products".
  R: O dedupe usa o contexto; confirmar que o template é renderizado no contexto do produto
     (com `product_template_id` no contexto).

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- O caminho dos assets aponta para `pg_attach_pdf_view/static/...`, mas a pasta do módulo é
  `pg_web_attach_pdf_view`. O caminho não corresponde, pelo que o JS do frontend NÃO é
  carregado tal como está. Corrigir o prefixo para o nome real do módulo.
- Várias entradas em `data`/`assets` estão comentadas (views de website e snippet, JS de limite).
- O agrupamento de documentos depende de convenções no NOME do ficheiro.
""",
    'author': 'Parâmetro Global SA',
    'depends': ['website_sale','base','web','product'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_attachment_access_rights.xml',
        'security/ir_attachment_rules.xml',
        'views/product_template_views.xml',
        #'views/website_product_template.xml',
        #'views/dynamic_snippet_filter.xml',
        
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_attach_pdf_view/static/src/js/attachment_preview.js',
            #'pg_attach_pdf_view/static/src/js/dynamic_snippet_limit.js',
        ],
    },
    'installable': True,
    'application': False,
}
