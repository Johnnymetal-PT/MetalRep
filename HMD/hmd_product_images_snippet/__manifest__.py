{
    "name": "HMD Product Images Snippet",
    "summary": "Galeria HTML editavel por produto na pagina do website (snippet de Studio gallery).",
    "version": "18.0.1.0.0",
    "category": "Website/Website",
    "author": "HMD / Parametro Global",
    "website": "https://www.hmd.pt",
    "license": "LGPL-3",
    "description": """
HMD Product Images Snippet (HMD)
================================

a) Objetivo de negocio
----------------------
No website builder, a HMD quer que cada pagina de produto tenha uma
zona de galeria editavel directamente pelo publisher (drag-and-drop
de imagens), por produto. O Studio gallery
(`x_studio_product_images`) cobre o backoffice mas nao expoe um
campo HTML editavel no site builder. Este modulo:
  - introduz `product.template.website_gallery_html` (Html) que
    guarda o markup do bloco editavel por produto;
  - se vazio, gera um default (4-cell grid) e auto-popula para
    publishers no primeiro acesso ao editor;
  - injecta o bloco editavel no template do produto antes do
    `product_detail_main`, com `data-oe-*` para que o editor saiba
    persistir;
  - helpers para iterar as imagens Studio em QWeb.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `website_sale`.
- (Opcional) Campo Studio `x_studio_product_images` no
  `product.template` se quiser usar os helpers
  `_get_gallery_images_for_template` e
  `_get_all_gallery_images_for_website`.

c) Como funciona (tecnico)
--------------------------
1. `product.template` (`models/product_template.py`):
   - `website_gallery_html` (Html, sanitize=False, html_translate):
     campo grande que persiste o markup editavel.
   - `write` override: se o utilizador atual e website publisher mas
     nao product manager, faz sudo() ao escrever o
     `website_gallery_html`. Isto permite a edicao no site builder
     sem ter ACL completo de produto.
   - `_get_gallery_images_for_template`: itera
     `x_studio_product_images` e devolve dicionarios com src/alt
     prontos para QWeb.
   - `_get_default_gallery_markup`: 4 cells com imagens default do
     `website` standard - serve de placeholder inicial.
   - `ensure_gallery_html_populated`: pre-popula o campo no primeiro
     acesso de publisher (chamado por QWeb helper).
   - `_get_gallery_html_for_website`: usado no template QWeb. Se
     tiver HTML guardado, devolve; senao gera o default e (se o
     editor esta ativo e o user e publisher) persiste com
     `skip_gallery_html` para evitar recursao.

2. Template QWeb (`views/product_template.xml`):
   - Herda `website_sale.product` e injeta uma seccao antes de
     `product_detail_main` com `oe_structure` + `data-oe-model`,
     `data-oe-id`, `data-oe-field="website_gallery_html"`. O editor
     do website reconhece e permite editar.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_product_images_snippet`.
2. Abrir a pagina de um produto no site (com publisher logged in).
3. Editar via "Edit" - aparece a zona de galeria como bloco
   editavel.
4. Arrastar imagens / texto / colunas. Guardar.
5. O HTML fica em `product.template.website_gallery_html` do
   produto especifico.

e) Exemplo pratico
------------------
Publisher abre /shop/sofa-lara, "Edit", arrasta 3 imagens de
ambiente para a galeria. Guarda.

Resultado:
  - `product.template[Sofa Lara].website_gallery_html` = HTML com
    as 3 imagens.
  - Outros produtos (sem editar) continuam com o markup default
    de 4 cells.

f) FAQ / Resolucao de problemas
-------------------------------
P: O editor nao deixa editar a galeria. Porque?
R: O utilizador tem de pertencer a `website.group_website_publisher`.
   Se nao tiver ACL ao produto, o `write` override faz sudo() para
   contornar - mas o campo precisa estar visivel na view (data-oe-id
   resolvido).

P: A galeria nao guarda. Verificar?
R: Verificar log "Persisting website_gallery_html for templates". Se
   nao aparece, a chamada via `data-oe-*` nao chegou ao write -
   pode ser bug no editor (Studio + builder, sequencia de saves).

P: Em traducao multilingue, o HTML guardado mantem-se igual em
   todos os idiomas?
R: Nao. O campo tem `translate=html_translate`. Cada idioma tem o
   seu HTML.

P: O default tem 4 cells fixas. Posso mudar?
R: Sim - alterar `_get_default_gallery_markup`. As imagens
   referenciam XIDs do website standard
   (`website.s_key_images_default_image_1` etc.). Garantir que
   continuam a existir em upgrade.

g) Pontos de atencao / avisos
-----------------------------
- `sanitize=False` no campo Html - intencional para permitir
  estruturas custom do editor; ATENCAO ao risco XSS se algum
  publisher injetar codigo malicioso.
- `sudo()` no write para publishers sem rights de produto - cuidado
  com edicoes laterais que possam ser elevadas indevidamente.
- O context flag `skip_gallery_html=True` evita recursao infinita
  no auto-populate.
- Em upgrade Odoo 19, validar que o editor continua a respeitar
  `data-oe-type="html"` em containers com `data-oe-field`.
""",
    "depends": [
        "website_sale",
    ],
    "data": [
        # "security/ir.model.access.csv",  # ACL declarada mas nao ativada
        "views/product_template.xml",
    ],
    "installable": True,
    "application": False,
}
