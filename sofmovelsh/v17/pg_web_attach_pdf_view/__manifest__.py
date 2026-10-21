{
    'name': 'PG Web Attachment PDF View',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Website',
    'summary': 'Permite ver anexos PDF do produto no website em nova aba, agrupados por tipo (Ficha Tecnica, 3D, ...).',
    'description': """
PG Web Attachment PDF View
==========================

a) Objetivo de negocio
----------------------
Na pagina publica do produto, mostrar os documentos associados ao produto
(`ir.attachment` ligados ao `product.template`) agrupados por tipo
("FICHA TECNICA", "CERTIFICADO DE CONFORMIDADE", "3D", "OUTROS") e abrir o
PDF em nova aba em vez de forcar download. Tambem ajusta o widget de
variantes para incluir o `discount_percentage` calculado entre
`compare_list_price` e `list_price`.

b) Pre-requisitos
-----------------
- Modulos: `website_sale`, `base`, `web`, `product`.
- `ir.attachment` ligados a `product.template` (`res_model='product.template'`,
  `res_id=<id>`). Carregados normalmente pelo workflow do
  [[pg_product_update]] (cria `product.document` em
  `process_additional_content`).

c) Como funciona
----------------
- `models/product_template.py`:
  - Em `product.template`:
    - `attachment_ids` (One2many com dominio sobre `ir.attachment`).
    - `all_category_names` (Char computed) - concatena nomes da cadeia de
      categorias separados por virgula (usado em snippets de website).
    - `_get_document_groups`: agrupa anexos por nome em 4 baldes:
      - "FICHA TECNICA" se nome tem "FICHA"
      - "CERTIFICADO DE CONFORMIDADE" se nome tem "CERTIFICADO"
      - "3D" se nome tem "3D"
      - "OUTROS" caso contrario
    - `_get_attachment_description`: helper para ler a descricao de um
      attachment.
- `controllers/variants.py`:
  - Override de `/website_sale/get_combination_info` (`type='json'`):
    - Calcula combination_info standard.
    - Acrescenta `discount_percentage` arredondado a unidade.
    - Renderiza o carousel via `website_sale.shop_product_images`.
- `static/src/js/attachment_preview.js`: JS frontend que abre PDFs em nova
  aba (registado em `web.assets_frontend`).
- `security/ir_attachment_access_rights.xml` + `ir_attachment_rules.xml`:
  garantem que os anexos do produto sao publicamente legiveis no website.
- `views/website_product_template.xml`: template QWeb que mostra os anexos
  na pagina do produto.

d) Passo a passo de utilizacao
------------------------------
1. Anexar PDFs ao produto (Backoffice / Produto / Documentos) com nomes que
   contenham as palavras-chave: "FICHA", "CERTIFICADO", "3D".
2. Publicar o produto no website.
3. Na pagina publica do produto, os documentos aparecem agrupados.
4. Clicar num documento abre o PDF em nova aba (graças ao JS).

e) Exemplo pratico
------------------
- Produto "Sofa Lisboa" com anexos:
  - "FICHA TECNICA - SOFA LISBOA.pdf"
  - "CERTIFICADO CONFORMIDADE.pdf"
  - "Modelo 3D Sofa Lisboa.glb"
  - "Manual de Montagem.pdf"
- Na pagina publica:
  - "FICHA TECNICA": ["FICHA TECNICA - SOFA LISBOA.pdf"]
  - "CERTIFICADO DE CONFORMIDADE": ["CERTIFICADO CONFORMIDADE.pdf"]
  - "3D": ["Modelo 3D Sofa Lisboa.glb"]
  - "OUTROS": ["Manual de Montagem.pdf"]

f) FAQ / Resolucao de problemas
-------------------------------
- "Anexo nao aparece":
  Confirmar que o `ir.attachment` tem `res_model='product.template'` e
  `res_id` correto. Se vier de outro modelo (ex. `product.product`), nao
  apanha.
- "PDF abre como download em vez de nova aba":
  Verificar que o JS `attachment_preview.js` esta a ser servido (recarregar
  com Ctrl+Shift+R, validar bundle frontend).
- "Categoria errada (acaba em OUTROS)":
  O agrupamento e por palavra-chave no nome do ficheiro. Renomear o
  ficheiro com a palavra-chave correta.

g) Pontos de atencao
--------------------
- As palavras-chave de agrupamento sao case-sensitive (`'FICHA' in name`);
  ficheiros com "ficha tecnica" em minusculas vao para "OUTROS". Manter
  convencao de upload em maiusculas.
- `discount_percentage` no controller usa `compare_list_price` e `list_price`;
  e independente do [[pg_descontos]] (que aplica ribbon/tag) e do
  [[pg_b2b_discounts]] (que aplica discount na linha).
- O nome do diretorio em `assets` (`pg_attach_pdf_view`) NAO bate com o
  nome do modulo (`pg_web_attach_pdf_view`); [PONTO POR VALIDAR] se o JS
  efectivamente carrega. Corrigir o asset path em
  `__manifest__.py` caso o ficheiro nao seja servido.

[FACTO OBSERVADO] o asset path declara
`pg_attach_pdf_view/static/src/js/attachment_preview.js` mas o ficheiro real
esta em `pg_web_attach_pdf_view/static/src/js/attachment_preview.js`. Validar
em runtime.
    """,
    'depends': ['website_sale', 'base', 'web', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_attachment_access_rights.xml',
        'security/ir_attachment_rules.xml',
        'views/product_template_views.xml',
        'views/website_product_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'pg_attach_pdf_view/static/src/js/attachment_preview.js',
        ],
    },
    'installable': True,
    'application': False,
}
