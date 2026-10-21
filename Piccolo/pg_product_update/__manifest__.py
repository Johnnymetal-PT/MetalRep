# -*- coding: utf-8 -*-
{
    'name': 'PG - Product Update',
    'version': '17.0.2.0.0',
    'summary': 'Walker recursivo de pasta de rede da Piccolo (\\\\192.168.5.5\\partilha geral\\1.PRODUTOS) que cria/atualiza categorias, web categories, atributos, imagens (template e variantes) e documentos do catalogo.',
    'description': """
PG Product Update
=================

a) Objetivo de negocio
----------------------
Sincronizar o catalogo Odoo com a estrutura de pastas mantida no
servidor de ficheiros da Piccolo (``\\\\192.168.5.5\\partilha geral\\1.PRODUTOS``).
A estrutura de pastas e que comanda: nomes de pasta viram nomes de
categoria, sub-pastas com "IMAGENS" indicam que aquela pasta e o
nivel do produto, ficheiros dentro de "IMAGENS" sao as fotos,
sub-pastas "COMPLEMENTOS" sao acessorios.

b) Pre-requisitos
-----------------
- Modulos standard ``product``, ``base``.
- Acesso de leitura ao share SMB ``\\\\192.168.5.5\\partilha geral\\1.PRODUTOS``
  a partir do servidor Odoo.
- Biblioteca Python ``PIL`` (Pillow) instalada.
- Convencoes de nomeacao das pastas:
  - Prefixos numericos ``"1. NOMEDOPRODUTO"`` sao removidos pelo
    ``normalize_folder_name`` (regex ``^\\d+\\.``).
  - Pastas com ``(PRODUTO)`` no nome sao saltadas.
  - Pasta ``IMAGENS`` (case-insensitive) marca o nivel do produto.
  - ``COMPLEMENTOS`` (acessorios) -> linkados como ``accessory_product_ids``.
  - Palavras-chave que NAO criam categoria: ``3D``, ``FICHA``,
    ``CERTIFICADO``. Pasta com estes nomes -> categoria pai
    propagada.
- Categoria publica ``Todas`` no website (ver pg_website).

c) Como funciona
----------------
- ``controllers/main.py``:
  - Rota ``/update_products`` (auth=user) - dispara o walker.
- ``models/product_category.py``: replica os mesmos campos
  ``cat_image_1`` / ``cat_image_2`` do ``pg_categories_image`` (NOTA:
  duplicacao - manter alinhado ou desativar um dos modulos).
- ``models/product_update.py`` (TransientModel ``product.update``):
  - ``update_products()``: ponto de entrada; cria categorias raiz
    ("All" / "Todas") e chama ``process_folders`` recursivo.
  - ``process_folders``: para cada pasta, se contiver subpasta
    ``IMAGENS`` -> ``process_product``. Senao desce na arvore
    criando ``product.category`` e ``product.public.category`` pela
    hierarquia.
  - ``process_product``: encontra o produto por nome (apos
    normalize), atribui categoria, publica no website, **apaga
    todos** os anexos/imagens previos do template e variantes e
    re-carrega.
  - ``upload_images``: itera ``IMAGENS``; imagens muito grandes
    (>50MP) sao redimensionadas com ``resize_image`` (PIL); evita
    duplicados por hash; cria ``product.image`` no template ou na
    variante consoante a estrutura de pastas (subpasta por variante).
  - ``process_additional_content``: carrega documentos (``product.document``)
    para folders fora de IMAGENS.
  - ``process_complementos_folder``: trata pastas COMPLEMENTOS como
    sub-produtos e linka-os ao produto pai via ``accessory_product_ids``.
  - ``add_categoria_attribute_to_product``: cria atributo dinamico
    no template quando ha pastas com nomes que combinam com valores
    existentes em ``product.attribute.value``.

d) Passo a passo de utilizacao
------------------------------
1. Instalar (garantir acesso SMB + Pillow).
2. Atualizar ficheiros no share (criar/mover/renomear pastas e
   imagens).
3. Browser autenticado: GET ``/update_products`` (ou clicar no botao
   "Atualizar Catalogo" se existir na vista).
4. O walker corre - logs em ``pg_product_update`` mostram cada
   passo. Pode demorar (varia com o tamanho do catalogo).

e) Exemplo pratico
------------------
Pasta ``\\1.PRODUTOS\\1. SALAS\\10. CADEIRAS\\Cadeira X\\IMAGENS\\``
contem ``capa.jpg`` e ``hover.jpg``.
Resultado:
- ``product.category`` "SALAS / CADEIRAS" criada.
- ``product.public.category`` "SALAS > CADEIRAS" idem (no website).
- Produto "Cadeira X" tem ``image_1920 = capa.jpg`` e
  ``product.image`` "hover.jpg" como imagem extra.
- Se houver sub-pasta IMAGENS/Linho Bege/ -> imagem associada a
  variante "Linho Bege".
- Se houver COMPLEMENTOS/Cadeira X Mesa/IMAGENS/ -> "Cadeira X Mesa"
  criada com imagens e linkada a "Cadeira X" como acessorio.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Root folder does not exist"* -> share SMB inacessivel a partir
  do servidor Odoo. Validar montagem ou credenciais.
- *"Product not found: <name>"* -> a pasta tem um nome que nao
  corresponde a nenhum ``product.template``. Carregar produtos
  via ``pg_product_upload`` primeiro ou renomear pasta.
- *"Imagens duplicadas"* -> hash check usa o ``base64`` da imagem
  inteira (`processed_images` em ``upload_images``). Para detetar
  duplicados visuais que diferem em bytes, e preciso comparacao
  perceptual (nao implementado).
- *"OOM em PIL"* -> imagens muito grandes (>50MP) sao redimensionadas
  automaticamente para max 1920x1920. Se ainda assim falhar, mover a
  imagem para um path mais pequeno antes.

g) Pontos de atencao / avisos
-----------------------------
- **HARDCODED**:
  - ``root_folder = "\\\\192.168.5.5\\partilha geral\\1.PRODUTOS"``.
  - ``\\1.PRODUTOS_2`` (alternativa local comentada).
- ``process_product`` faz **unlink** dos anexos e imagens existentes
  antes de re-carregar. Se houver imagens uploaded manualmente, **vao
  ser apagadas** a cada sync.
- ``rota /update_products`` retorna HTML literal "Products updated
  successfully!" sem feedback estruturado.
- ``cat_image_1`` / ``cat_image_2`` aqui DUPLICAM os campos do
  ``pg_categories_image``. Investigar e remover de um dos lados.
- ``Image.ANTIALIAS`` esta deprecated em Pillow 10.x; substituir
  por ``Image.Resampling.LANCZOS`` numa proxima iteracao.
- Walker e single-thread e sequencial; em catalogo grande pode
  demorar minutos. Aceitavel pela frequencia (1x/dia/semana).
""",
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['base', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_update_view.xml',
    ],
    'installable': True,
    'application': False,
}
