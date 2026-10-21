{
    'name': 'PG Product Update',
    'version': '2.0',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'category': 'Inventory',
    'summary': 'Atualiza produtos a partir de uma estrutura de pastas no servidor (imagens, anexos, categorias).',
    'description': """
PG Product Update
=================

a) Objetivo de negocio
----------------------
Atualizar em massa produtos no Odoo a partir de uma estrutura de pastas
mantida no servidor de ficheiros (caminho actual hardcoded:
`/ProgGest/Odoo/Clientes/SofMovel/1.PRODUTOS`). Cada pasta de produto traz:
- pasta IMAGENS (com as imagens do produto e variantes em subpastas);
- pasta COMPLEMENTOS (com produtos complementares, ligados como acessorios);
- ficheiros adicionais (3D, fichas tecnicas, certificados, etc.) que sao
  publicados como `product.document` da pagina do produto.

O modulo cria a arvore de categorias internas/eCommerce/POS a partir da
arvore de pastas, faz upload das imagens (com resize >50MB, dedup por SHA256),
publica o produto e envia email de notificacao no fim. E executado por um
endpoint HTTP `/update_products` ou pelo botao `update_product_data` no produto.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`.
- Bibliotecas Python: `PIL` (Pillow), `psutil` (opcional, para logs de memoria).
- Caminho `/ProgGest/Odoo/Clientes/SofMovel/1.PRODUTOS` acessivel pelo Odoo
  (montagem partilhada de NAS).
- Template de email `mail.template` com ID 79 - usado pela notificacao no fim.
- Categorias raiz "All" (`product.category`) e "Todas"
  (`product.public.category`).

c) Como funciona
----------------
- `models/product_category.py`: adiciona `cat_image_1` e `cat_image_2` em
  `product.category` para guardar as imagens da categoria (usadas no
  website).
- `models/product_update.py`:
  - Modelo `product.update` que orquestra todo o processo:
    - `process_folders_iteratively`: percorre a arvore de pastas com stack
      iterativa (para evitar recursion limit).
    - `process_product`: faz match do produto via `default_code`, limpa
      anexos e imagens previas, sobe a estrutura nova e cria atributo
      "Categoria" se houver variantes.
    - `upload_images`: deduplica por SHA256, faz resize se imagem > 50MB,
      primeira imagem de "IMAGENS" e thumbnail, restantes sao
      `product.image`; imagens em pastas de variante sao atribuidas as
      variantes correspondentes.
    - `process_complementos_folder`: liga produtos da pasta COMPLEMENTOS
      como `accessory_product_ids` do produto principal.
    - `process_additional_content`: cria `product.document` para ficheiros
      nao-IMAGENS, com `shown_on_product_page=True`.
  - `update_products`: ponto de entrada com retry em
    `SerializationFailure` (5 tentativas) e envio de email final via
    template ID 79.
  - `send_email_notification`: usa `mail.template.browse(79)`.
  - Em `product.template`: metodo `update_product_data` que chama
    `update_products()`.
- `controllers/main.py`: rota `/update_products` (`auth='user'`) que dispara
  o mesmo `update_products()` via HTTP.

d) Passo a passo de utilizacao
------------------------------
1. Garantir que `/ProgGest/Odoo/Clientes/SofMovel/1.PRODUTOS` esta montado e
   visivel pelo processo Odoo.
2. Os produtos a atualizar devem existir no Odoo com `default_code` igual ao
   nome da pasta (apos `normalize_folder_name` - remove prefixo "NN.").
3. Acionar:
   - HTTP: `GET /update_products` (autenticado).
   - Backoffice: vista do produto -> botao que invoca `update_product_data`
     (associado em `views/product_update_button.xml`).
4. No fim, o utilizador recebe email a partir do template ID 79.

e) Exemplo pratico
------------------
- Pasta `1.PRODUTOS/1.Sofas/02. SOF-001/IMAGENS/` contem 5 imagens.
- O produto `default_code = "SOF-001"` no Odoo:
  - Recebe a 1a imagem como `image_1920`;
  - As outras 4 ficam como `product.image` adicionais;
  - Categoria "1.Sofas" (normalizada "Sofas") e atribuida em `categ_id`,
    `public_categ_ids` e `pos_categ_ids`;
  - `is_published = True`.
- Se houver `1.PRODUTOS/1.Sofas/02. SOF-001/3D/modelo.glb`:
  - E criado um `product.document` com o ficheiro, `shown_on_product_page=True`.

f) FAQ / Resolucao de problemas
-------------------------------
- "Root folder does not exist":
  O caminho hardcoded nao esta montado. Confirmar mount/symlink antes de
  acionar.
- "Email nao chegou":
  Confirmar que o template ID 79 ainda existe (`mail.template`). O log
  indica "Email template with ID 79 not found." quando falha.
- "Produto nao encontrado":
  O modulo procura por `default_code = normalize_folder_name(nome_pasta)`.
  Se a pasta nao tiver o codigo correto, o produto e ignorado.
- "Imagens nao aparecem na variante":
  As subpastas de IMAGENS sao tratadas como nomes de variante. Confirmar
  que existe `product.attribute.value` com esse nome; caso contrario, o
  modulo loga warning e nao associa.

g) Pontos de atencao
--------------------
- Caminho `/ProgGest/Odoo/Clientes/SofMovel/1.PRODUTOS` esta hardcoded em
  `update_products`; portar para configuracao (`ir.config_parameter`) e
  trabalho futuro.
- Template ID 79 esta hardcoded. Se for recriado o ID muda.
- O modulo apaga `ir.attachment` e `product.image` do produto antes de subir
  os novos. Reprocessamentos perdem qualquer imagem que tenha sido carregada
  manualmente.
- `Image.ANTIALIAS` (em `resize_image`) foi removido nas versoes recentes do
  Pillow. Para Pillow >= 10 trocar por `Image.LANCZOS`.

[FACTO OBSERVADO] depende de partilha de ficheiros do cliente.
[PONTO POR VALIDAR] frequencia de execucao e impacto em performance ao apagar
todas as imagens existentes antes de reupload.
    """,
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_update_view.xml',
        'views/product_update_button.xml',
    ],
    'installable': True,
    'application': False,
}
