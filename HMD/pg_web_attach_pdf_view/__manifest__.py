{
    'name': 'PG Web Attachment PDF View',
    'version': '18.0.1.0.0',
    'category': 'Website',
    'summary': 'Mostra anexos do produto (PDFs, fichas tecnicas, 3D) em accordion no site, ligados a variante.',
    'description': """
PG Web Attachment PDF View (HMD)
================================

a) Objetivo de negocio
----------------------
A HMD quer que cada produto no site mostre uma area "Documentos" com
ficheiros agrupados por tipo (Ficha Tecnica, Certificado de
Conformidade, 3D) e que esses documentos filtrem automaticamente
conforme as variantes selecionadas pelo cliente (ex.: ao escolher uma
cor de tecido, so aparecem as fichas tecnicas relativas a essa cor).
Tambem expoe um separador "Documentos" no backoffice do produto e
abre acesso de leitura a anexos para utilizadores portal e publicos.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `website_sale`, `base`, `web`, `product`.
- Estrutura de nomes dos anexos: a logica de agrupamento usa SUBSTRING
  MATCH no `name` do `ir.attachment`:
    - se contem "3D"        -> grupo "3D"
    - se contem "CERTIFICADO" -> "CERTIFICADO DE CONFORMIDADE"
    - se contem "FICHA"     -> "FICHA TECNICA"
  Sem nenhuma dessas substrings, o anexo nao e mostrado.
- Os anexos devem usar a convencao do nome com " >> " como separador
  hierarquico (ex.: "FICHA TECNICA >> Cor Azul >> ficha.pdf"). O JS no
  template usa isto para decidir se o anexo combina com a variante
  selecionada (ver FAQ).

c) Como funciona (tecnico)
--------------------------
1. `product.template` (`models/product_template.py`):
   - `attachment_ids` (Many2many filtrado): aponta para `ir.attachment`
     onde `res_model='product.template'`. Permite editar anexos no
     produto sem sair do form.
   - `all_category_names` (computed): juntos os nomes das categorias
     hierarquicas do produto separados por virgula (util para
     filtrar/snippets).
   - `_get_document_groups()`: arruma os anexos em 3 grupos pelo nome
     (case-sensitive): `3D` e `FICHA TECNICA` por substring, `IMAGENS HR`
     por PREFIXO (o nome tem de comecar por 'HR'). O prefixo evita falsos
     positivos - ha nomes reais com 'HR' no meio, ex. 'VALCHROMAT'.
     O grupo 'CERTIFICADO DE CONFORMIDADE' existiu ate 2026-07-29 e foi
     substituido por 'IMAGENS HR' a pedido da HMD (tarefa 6604); nao havia
     nenhum anexo com 'CERTIFICADO' no nome, logo nada se perdeu.
   - `_get_attachment_description(id)`: helper para QWeb obter a
     descricao de um anexo.

2. View backoffice (`views/product_template_views.xml`): aba
   "Documentos" com `attachment_ids` em widget many2many_binary.

3. Template QWeb (`views/website_product_template.xml`): herda
   `website_sale.product` e injeta um accordion Bootstrap com 2 secoes
   visiveis (Detalhes Tecnicos + Documentos) e uma 3a comentada
   (Variantes do produto). Renderiza os documentos por grupo, com link
   `target="_blank"` para `/web/content/<id>` (abre em nova tab; o
   browser mostra o PDF inline se tiver leitor).
   JS no proprio template:
     - intercepta cliques no accordion para abrir/fechar manualmente
       (substitui o Bootstrap collapse para corrigir um bug com
       multiplos accordions abertos);
     - `alertActiveVariants()` le radios/selects de variantes ativos e
       compara com o nome dos anexos no formato
       `"GRUPO » Atributo1 » Atributo2 » nome.pdf"` para esconder
       anexos que nao combinam.
       ATENCAO: o separador real, tanto no template (`rpartition(' » ')`)
       como no JS (`split(' » ')`), e ` » ` (U+00BB). Esta documentacao
       dizia ` >> `, o que levava a nomes que o filtro nao reconhece.
       Corrigido 2026-07-29. Verificado em producao nessa data: ZERO dos
       4060 anexos de `product.template` usa qualquer dos separadores,
       pelo que a filtragem por variante nunca chega a atuar.

4. Snippet dinamico (`views/dynamic_snippet_filter.xml`):
   `s_dynamic_snippet_products` standalone com domain
   `sale_ok+website_published` para reutilizacao no editor de website
   (carrosel horizontal de produtos).

5. Seguranca:
   - `security/ir.model.access.csv`: leitura de `product.template` e
     `ir.attachment` para `base.group_user` (RWUD=1,0,0,0).
   - `security/ir_attachment_access_rights.xml`: dar perm_read sobre
     `ir.attachment` a `base.group_portal`.
   - `security/ir_attachment_rules.xml`: 2 `ir.rule` que permitem a
     portal e publico ler anexos cujo `res_model` seja
     `product.template` ou `product.product`. Isto e o que faz
     funcionar o link `/web/content/<id>` para visitantes anonimos.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_web_attach_pdf_view` na BD HMD.
2. Inventario > Artigos > abrir um produto > aba "Documentos".
3. Carregar PDFs/imagens com nome respeitando a convencao:
     "FICHA TECNICA >> ficha_geral.pdf"
     "FICHA TECNICA >> Azul >> ficha_azul.pdf"
     "CERTIFICADO DE CONFORMIDADE >> certificado.pdf"
     "3D >> modelo.glb"
4. Publicar o produto no website (`is_published=True`).
5. Visitar `/shop/<produto>`. Aparece o accordion com as secoes
   "Detalhes Tecnicos" e "Documentos". Ao clicar em "Documentos", ve
   os ficheiros agrupados por tipo.
6. Selecionar variantes - os ficheiros que nao combinam com as
   variantes selecionadas desaparecem.

e) Exemplo pratico
------------------
Produto "Sofa A" com variantes Cor = [Azul, Vermelho].
Anexos:
  - "FICHA TECNICA >> ficha_comum.pdf"   (visivel sempre)
  - "FICHA TECNICA >> Azul >> ficha_azul.pdf" (so quando Cor=Azul)
  - "FICHA TECNICA >> Vermelho >> ficha_red.pdf" (so quando Cor=Vermelho)

Cliente no /shop seleciona Cor=Azul -> ve "ficha_comum.pdf" e
"ficha_azul.pdf"; "ficha_red.pdf" fica escondida.

f) FAQ / Resolucao de problemas
-------------------------------
P: Adicionei um anexo mas nao aparece no site. Porque?
R: 3 hipoteses:
   1. O nome nao contem "FICHA" / "CERTIFICADO" / "3D". O
      `_get_document_groups` filtra por substring.
   2. O anexo nao esta em `attachment_ids` (verificar a aba
      Documentos no backoffice).
   3. O publico nao tem leitura ao anexo. Validar que as `ir.rule` de
      portal/publico estao ativas.

P: O accordion fica sempre fechado quando clico. Porque?
R: O JS substitui o comportamento padrao do Bootstrap collapse. Se ha
   outro modulo a manipular `.accordion-button`, podem entrar em
   conflito. Verificar a consola do browser.

P: A filtragem por variante nao funciona. Como debugar?
R: O JS le `data-partition` dos `.attachment-item` e usa o separador
   " >> " para extrair atributos. Se renomeou o anexo manualmente sem
   respeitar o formato, o filtro nao reconhece. Existem `console.log`
   nas funcoes para diagnostico.

P: O carrosel de imagens do produto auto-avancava antes. Foi removido?
R: Esta comentado no template (`<!--// Auto-switch carousel -->`).
   Removido por bug com zoomodoo-flyout (zoom inline). Reativar
   apenas depois de validar a interacao.

P: Portal/publico nao consegue abrir o PDF (404 ou erro). Porque?
R: Falta uma das `ir.rule` deste modulo. Reinstalar/atualizar para
   recriar as regras.

g) Pontos de atencao / avisos
-----------------------------
- ESTILO INLINE no template (`style="margin-bottom: 5%; width: 40%;
  margin-left: 10%;"`). Em responsive, validar em mobile.
- O ficheiro CSS comenta o JS `attachment_preview.js` - existe no
  modulo mas nao esta a ser carregado. Remover se nao for usado.
- HARDCODED: nomes dos grupos "FICHA TECNICA", "CERTIFICADO DE
  CONFORMIDADE", "3D" em portugues. Se o cliente quiser i18n, evoluir
  para uma tabela de mapping.
- O ACL `access_ir_attachment_user` esta a 1,0,0,0 - apenas leitura
  para internos. Cruzar com `pg_attachment_universal_access` para nao
  conflituar - ver overrides nesse modulo.
- Multiplas funcoes JS duplicadas (`getVariantName`,
  `alertActiveVariants` aparecem duas vezes) - oportunidade de
  limpeza, mas nao bloqueante.
""",
    'author': 'Parametro Global SA',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['website_sale', 'base', 'web', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_attachment_access_rights.xml',
        'security/ir_attachment_rules.xml',
        'views/product_template_views.xml',
        'views/website_product_template.xml',
        'views/dynamic_snippet_filter.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            #'pg_attach_pdf_view/static/src/js/attachment_preview.js',
            'pg_web_attach_pdf_view/static/src/css/styles.css',
        ],
    },
    'installable': True,
    'application': False,
}
