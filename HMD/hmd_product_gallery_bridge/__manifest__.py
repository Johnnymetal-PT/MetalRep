# -*- coding: utf-8 -*-
{
    "name": "HMD Product Gallery Bridge",
    "version": "18.0.1.0.0",
    "summary": "Espelha a galeria Studio do produto (x_studio_product_images) para ir.attachment editaveis no website.",
    "description": """
HMD Product Gallery Bridge
==========================

a) Objetivo de negocio
----------------------
A galeria de imagens dos produtos HMD vive num campo One2many criado
em Studio: `x_studio_product_images` (geralmente apontando a
`product.image` ou modelo Studio). O website standard `website_sale`
nao sabe ler diretamente esse campo - precisa de `ir.attachment` no
modelo `product.template`. Este modulo "faz a ponte": para cada record
da galeria Studio, mantem um `ir.attachment` espelho associado ao
template, com o conteudo, mimetype e metadados sincronizados. Resultado
pratico: a galeria Studio aparece no site e fica disponivel para edicao
no website builder como qualquer outro attachment.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `website_sale`.
- Campo Studio `x_studio_product_images` no `product.template`,
  apontando a `product.image` (typical) ou a `ir.attachment`.
- Se for `product.image`, o `product_template_attachment_ids` do
  modulo Studio precisa estar configurado para que cada imagem aponte
  ao template (`product_tmpl_id`) ou variante (`product_variant_id`).

c) Como funciona (tecnico)
--------------------------
1. `product.image` (`models/product_image.py`):
   - Adiciona `hmd_attachment_id` (Many2one ir.attachment, copy=False,
     readonly=True): o attachment espelho.
   - `_sync_hmd_attachment()`: lifecycle hook chamado em create,
     write e atraves de `_ensure_hmd_attachment_bridge`. Para cada
     imagem:
       - le o payload (tenta `image_1920`, `image_1024`, ..., depois
         `attachment_id.datas`);
       - obtem o template do produto (template direto ou variante);
       - se nao houver template ou nao houver datas, apaga o
         attachment ponte; salta;
       - prepara `vals` com `res_model='product.template'`,
         `res_id=template.id`, `public=True`, `company_id`;
       - cria ou atualiza o `ir.attachment` ponte (diff fields-only);
       - atualiza `image.hmd_attachment_id` (com flag context
         `hmd_gallery_bridge_skip=True` para evitar recursao);
       - normaliza `company_id` do attachment.
   - `unlink`: cascata - apaga o attachment ponte quando a imagem e
     apagada.

2. `product.template` (`models/product_template.py`):
   - `hmd_studio_gallery_attachment_ids` (Many2many computed,
     `store=False`): para cada template, agrega os attachments-ponte
     da galeria Studio. `depends` em
     `x_studio_product_images` e `image_1920`.
   - Compute reusa `_ensure_hmd_attachment_bridge` se a galeria for
     `product.image`; reusa diretamente se for `ir.attachment`; cria
     attachments inline a partir de `image_1920` para outros modelos
     Studio.
   - `_get_hmd_studio_gallery_items()`: helper usado em templates
     QWeb. Devolve dicionarios com src, alt, mimetype, dimensoes,
     compativel com a interface que o `website_sale` usa.

d) Passo a passo de utilizacao
------------------------------
1. Configurar em Studio o campo `x_studio_product_images` no
   `product.template` (One2many a `product.image` ou similar).
2. Instalar `hmd_product_gallery_bridge`.
3. Em qualquer template QWeb HMD que precise da galeria, chamar
   `t-set="items" t-value="product._get_hmd_studio_gallery_items()"` e
   iterar sobre items.
4. Adicionar/editar imagens no produto via Studio - o sync e
   automatico.

e) Exemplo pratico
------------------
Produto "Sofa Modelo Lara" com 3 imagens em x_studio_product_images.
Apos instalacao:
  - cria 3 `ir.attachment` com `res_model='product.template'` e
    `res_id=<id do Lara>`, `public=True`;
  - `hmd_studio_gallery_attachment_ids` agrega os 3;
  - QWeb itera e renderiza no website com `image_url`/`website_url`.

Apagar uma imagem em Studio -> o attachment espelho e apagado.

f) FAQ / Resolucao de problemas
-------------------------------
P: A galeria nao aparece no site. Porque?
R: 4 hipoteses:
   1. O campo Studio nao se chama `x_studio_product_images` (ver
      Studio).
   2. As imagens Studio nao tem datas (vazias).
   3. O template QWeb que renderiza a galeria nao chama
      `_get_hmd_studio_gallery_items()`.
   4. O publico/portal nao tem leitura aos attachments (validar
      record rules + `pg_attachment_universal_access`).

P: Editei uma imagem em Studio e o site continua com a antiga.
R: O write em `product.image` chama `_sync_hmd_attachment`. Se nao
   resolveu, verificar que nao foi escrito com
   `context.hmd_gallery_bridge_skip=True` (deixa de propagar).
   Forcar: `product.image.browse(id)._ensure_hmd_attachment_bridge()`.

P: O attachment espelho desapareceu mas a imagem Studio existe.
R: O sync apaga o espelho quando nao consegue obter `datas` ou nao
   tem template. Se a galeria mudou de produto, o sync recria
   automaticamente. Reabrir o produto/correr o compute deve resolver.

P: Os attachments aparecem com nomes feios ("Product Image"). Como
   melhorar?
R: O `_prepare_hmd_attachment_vals` usa `self.name` ou
   `template.name`. Garantir que a imagem Studio tem `name` definido.

g) Pontos de atencao / avisos
-----------------------------
- DEPENDENCIA STUDIO: `x_studio_product_images`. Se o cliente
  renomear o campo Studio, este modulo deixa de funcionar
  silenciosamente. Em upgrade, validar.
- `public=True` nos attachments espelho - intencional (galeria de
  loja online). Cuidado se houver imagens internas/confidenciais
  no Studio.
- Usa `sudo()` em quase todos os ramos - intencional para nao tropecar
  em ACL e poder gerir attachments. Garantia: o utilizador final que
  cria a imagem tem que ter acesso ao produto e o efeito final ja
  esta exposto a publico via `public=True`.
- A flag context `hmd_gallery_bridge_skip=True` evita recursao no
  write - se outro modulo escrever em `product.image` com esta flag,
  o sync nao corre (intencional).
- Em upgrade Odoo 19, validar que `original_id` em ir.attachment
  continua a existir (usado em `_prepare_hmd_gallery_item_from_attachment`).
- O modulo nao tem ficheiros XML (`data: []`). Toda a logica e Python.
""",
    "author": "HMD / Parametro Global",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": [],
    "installable": True,
    "application": False,
}
