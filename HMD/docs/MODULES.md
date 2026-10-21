# Inventario de Custom Modules - HMD

> Referencia rapida dos modulos presentes no repositorio HMD para Odoo 18.0
> Enterprise.
>
> **Para o guia detalhado de cada modulo** (objetivo, pre-requisitos, passo a
> passo, exemplo, FAQ, avisos), consultar o campo `description` do
> `__manifest__.py` do proprio modulo. Esta convencao esta definida em
> `.pg_framework/templates/AGENTS_SHARED.md` -> "Documentacao obrigatoria de
> modulos custom".

## Convencao de novos modulos custom

Toda a criacao ou atualizacao de modulo custom (`pg_*` ou `hmd_*`) deve
trazer, na MESMA entrega:

1. **Comentarios no codigo** (PT por defeito):
   - docstring de topo em cada ficheiro Python relevante;
   - comentarios inline nos pontos NAO obvios (overrides, IDs fixos,
     gatilhos, efeitos colaterais, `sudo`, `with_user`, etc.);
   - nao comentar o obvio.

2. **`__manifest__.py` rico**:
   - `summary`: 1 linha em PT;
   - `description`: guia completo em 7 seccoes:
     a) Objetivo de negocio;
     b) Pre-requisitos;
     c) Como funciona (tecnico);
     d) Passo a passo de utilizacao;
     e) Exemplo pratico;
     f) FAQ / Resolucao de problemas;
     g) Pontos de atencao / avisos.

3. **Distincao de evidencia** (quando relevante):
   `FACTO OBSERVADO` vs `INFERENCIA` vs `PONTO POR VALIDAR`.

Modulos obsoletos sao excecao: basta nota de OBSOLETO + substituto.

Esta regra esta automaticamente exigida pelo framework PG para qualquer
proximo `pg_*`/`hmd_*` que se crie ou atualize neste repositorio - nao
ha trabalho adicional a fazer alem de seguir o template.

## Modulos custom HMD / Parametro Global

### Vendas & CRM
- **hmd_sale_price_calculator** - Calculadora de preco por linha de venda
  com fallback de custo (standard_price -> ultima PO -> BoM agregada por
  fornecedor) + margem fixa/percentual + observacao guardada.
- **hmd_sale_product_image_once** - A imagem da linha de venda (campo
  Studio `x_studio_imagem_do_produto`) e preenchida UMA VEZ a partir do
  produto e respeita edicoes manuais a partir dai.
- **pg_crm_project_opportunities** - Liga `crm.lead` a `project.project`
  com smart button e fallback automatico via `sale.order.project_id`.
- **pg_sale_purchase_link** - Smart buttons "Purchase Orders" e
  "Manufacturing Orders" no SO (ligacao pelo procurement_group) +
  sincronizacao do `origin` quando o SO muda de nome.

### Compras
- **hmd_product_rfq_button** - Smart button "RFQs" no produto que mostra
  POs em TODOS os estados (nao so confirmadas).
- **hmd_purchase_history_all** - Relaxa a view SQL standard
  `purchase.history.list` para mostrar POs em qualquer estado +
  sanitiza dominios das `action_view_po` em produto/variante/supplier.
- **hmd_purchase_image_toggle** - Sincroniza o flag Studio
  `imprimir_todas_imagens` (cabecalho da PO) com `imprimir_imagem` por
  linha; respeita edicoes manuais.
- **pg_supplierinfo_purchase** - Botao "Create RFQ" direto na linha de
  fornecedor (`product.supplierinfo`); abre PO em draft com tudo
  preenchido a partir da linha.

### Producao & Materiais
- **hmd_mrp_product_button** - Link "Ver Produto" em cada linha de BoM e
  em `move_raw_ids` / `move_finished_ids` da MO.
- **pg_price_table** - Tabela de "aproveitamento de tecido" (10 colunas)
  no produto; aplica automaticamente a quantidade correcta de tecido na
  MO ao criar. (NOTA: campos chamam-se `price_*` mas guardam METROS, nao
  precos - razoes historicas.)
- **pg_tecidos** - Customizacao da BoM por MO conforme descricao de
  variantes na venda (regex parsing); duplica BoM, ajusta consumos de
  tecido, cria/reutiliza componentes derivados, atribui fornecedor.
- **pg_packing_list** - Packing list personalizado: volumes, dimensoes
  (ate 6 volumes), peso, cubicagem ao produto/venda/entrega com wizard
  para calculo manual. Regra HMD: peso estimado = cubicagem * 80.

### Produtos & Website
- **hmd_product_project_button** - Smart button "Projetos" no produto:
  agrega projetos ligados via SO/PO com `project_id`.
- **hmd_product_gallery_bridge** - Espelha a galeria Studio
  `x_studio_product_images` para `ir.attachment` editaveis no website
  builder e por modulos QWeb.
- **hmd_product_images_snippet** - Galeria HTML editavel por produto na
  pagina do website (snippet de Studio gallery + helpers QWeb).
- **hmd_product_tag_project_link** - Tags do produto clicaveis no /shop
  apontando para paginas de projeto/portfolio (override QWeb + fallback
  JS para themes resistentes).
- **hmd_website_editor_diagnostics** - Endpoint backoffice
  `/hmd/website_editor_diagnostic` que gera relatorio HTML de tudo o que
  pode estar a impedir a edicao de uma pagina do website.
- **pg_shop_public_override** - Mantem `/shop` acessivel a publico,
  publica catalogo simplificado `/artigos` e rota dinamica
  `/smart-shop`.
- **pg_web_attach_pdf_view** - Mostra documentos (PDF, fichas, 3D) no
  website em accordion, agrupados por tipo (convencao de nome dos
  anexos) e filtrados por variante selecionada.

### Contabilidade & Permissoes
- **pg_account_journal_access** - Whitelist por utilizador no
  `account.journal` (ver/criar/editar/lancar). Pre-seed automatico dos
  Admins Contab. Funciona via `ir.rule` globais.
- **pg_attachment_universal_access** - Override cirurgico ao `ir.attachment`
  para que TODOS os utilizadores internos vejam todos os anexos da BD,
  ignorando o check ao registo-pai. Mantem proteccoes para
  portal/publico, anexos orfaos e campos binarios restritos por
  `res_field.groups`.

## Modulos de TERCEIROS no repositorio

> Estes modulos foram trazidos para o repositorio mas NAO foram criados
> pela HMD/Parametro Global. A documentacao definitiva vive nos
> repositorios upstream. Em upgrade/sync, podem ser substituidos. Nao
> reescrever o `__manifest__.py` deles sem avisar - perde-se quando se
> faz pull do upstream.

- **pg_multi_discount** - Softhealer Technologies (multi-discount em SO/PO/IN).
- **pg_email_cc** - Techultra Solutions (CC em mail composer).
- **pg_product_multi_attachment** - Cybrosys (multiplos anexos por produto).
- **pg_website_hide_unavailable_variant** - ErpMstar (esconder variantes
  indisponiveis no /shop).
- **pg_3d_ecommerce** - OCA (3D viewer no website_sale).
- **pg_3d_viewer** - OCA (widget 3D base).
- **pg_product_model_viewer** - OCA (3D viewer em produto backoffice).
- **pg_website_attribute_image** - Visionee (imagens em valores de
  atributo no website).
- **sale_advance_payment** - OCA / Comunitea (adiantamentos em SO).
- **ptplus_sale_advance_payment** - Exo Software (localizacao PT do
  acima, auto-install com `ptplus_sale`).

## Estado obsoleto

(Nenhum modulo neste repositorio esta marcado como obsoleto a
2026-05-28. Se um for declarado obsoleto, sinalizar no
`__manifest__.py` com nota OBSOLETO + indicacao do modulo substituto,
conforme convencao do AGENTS_SHARED.)
