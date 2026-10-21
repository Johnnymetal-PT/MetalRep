{
    'name': 'HMD Product Tag Project Link',
    'version': '18.0.1.0.8',
    'category': 'Website',
    'summary': 'Liga tags do produto a paginas de projeto no site (override QWeb + fallback JS).',
    'author': 'HMD / Parametro Global',
    'license': 'LGPL-3',
    'description': """
HMD Product Tag Project Link (HMD)
==================================

a) Objetivo de negocio
----------------------
Cada produto pode ter tags ligadas a paginas de portfolio no website
(ex.: tag "Projeto Hotel X" -> /portfolio/hotel-x). Nas paginas de
produto no /shop, queremos que essas tags fiquem clicaveis e levem
diretamente para o respetivo projeto. O standard renderiza tags como
simples spans - este modulo:
  - adiciona campo `hmd_project_page_url` ao `product.tag`;
  - override QWeb da template `website_sale.product_tags` para
    envolver cada tag num `<a>` para a URL configurada;
  - fallback JS (carregado em `website.layout`) que, em paginas onde
    o override QWeb nao foi aplicado (themes/Studio agressivos),
    consulta um endpoint JSON com as URLs e converte as tag-spans
    em links clicaveis dinamicamente.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `website_sale`.

c) Como funciona (tecnico)
--------------------------
1. `product.tag` (`models/product_tag.py`): novo campo
   `hmd_project_page_url` (Char). Preencher com URL relativa ou
   absoluta (ex.: "/portfolio/hotel-x" ou "https://...").

2. `controllers/main.py`: endpoint
   `GET /hmd/product_tag_project_urls/<int:product_tmpl_id>` ->
   JSON `{"tag_urls": {"NomeTag": "/url"}}`. So inclui tags com
   `visible_on_ecommerce=True` e `hmd_project_page_url` nao-vazio.
   Normaliza a URL: se nao comecar por `/`, `http://`, `https://`,
   prefixa `/`.

3. Templates QWeb:
   - `views/product_tag_views.xml`: adiciona o campo URL ao form e
     a tree de product.tag no backoffice.
   - `views/website_product_template.xml`: override (priority 9999)
     a `website_sale.product_tags`. Cada tag e renderizada dentro
     de `<a t-att-href="project_url">` se URL existir, caso
     contrario span normal. Replica o estilo standard (image +
     fallback colorido).
   - `views/website_layout_fallback.xml`: injecta um <script>
     inline em `website.layout` que:
       1. obtem `product_tmpl_id` do `#product_details`;
       2. faz fetch ao endpoint JSON;
       3. percorre `.badge`, `.o_tag_badge`, `.text-nowrap` dentro
          de `#product_details`, encontra spans cujo texto bate
          certo com o nome da tag, e poe-os clicaveis via
          `data-hmd-project-url` + listener click/Enter;
       4. MutationObserver re-aplica em re-render do shop.
   Este fallback existe porque alguns themes (em particular
   theme_party_planner) nao respeitam o override QWeb.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_product_tag_project_link`.
2. Inventario > Configuracao > Product Tags > abrir uma tag (ex.
   "Hotel X"). Preencher "Project Page URL" com `/portfolio/hotel-x`.
3. Ligar a tag a produtos. Garantir `visible_on_ecommerce=True`.
4. No website, abrir a pagina /shop do produto. As tags do produto
   aparecem clicaveis e levam para o portfolio.

e) Exemplo pratico
------------------
Tag "Hotel X" -> URL "/portfolio/hotel-x".
Produto "Sofa Lara" tem a tag "Hotel X".
Visitante visita /shop/sofa-lara, ve a tag, clica -> navega para
/portfolio/hotel-x.

Se o tema sobrescreveu o template product_tags, o JS fallback
deteta o span e mantem-no clicavel.

f) FAQ / Resolucao de problemas
-------------------------------
P: A tag aparece como span sem link.
R: Verificar:
   1. URL preenchida (em branco -> nao gera link);
   2. `visible_on_ecommerce` ativo na tag;
   3. Override QWeb activo (Settings > Technical > Views, procurar
      "website_sale_product_tags_direct_project_link"). Se inativo,
      o JS fallback ainda assim deveria funcionar.

P: O JS fallback nao bate certo. Porque?
R: Os selectors do JS (`#product_details .badge`, `.text-nowrap`)
   podem nao apanhar a estrutura real do theme. Inspecionar e
   ajustar.

P: A URL aparece sempre com /portfolio/...?
R: O controller normaliza a URL: se nao comeca por `/`, `http://` ou
   `https://`, prefixa `/`. Para URLs absolutas, escrever
   completas.

g) Pontos de atencao / avisos
-----------------------------
- O JS fallback inline em `website.layout` corre em TODAS as
  paginas do site, mas so faz fetch quando deteta
  `#product_details`. Custo desprezavel.
- O endpoint e `auth='public'` e devolve apenas dados que ja sao
  publicos (tags ecommerce-visible com URL ja exposta no site).
  Sem risco de leak.
- Suporta absolute URLs (http/https) ou relativas. Sempre que
  comecar por `/`, e tratada como interna.
""",
    'depends': ['website_sale'],
    'data': [
        'views/product_tag_views.xml',
        'views/website_product_template.xml',
        'views/website_layout_fallback.xml',
    ],
    'installable': True,
    'application': False,
}
