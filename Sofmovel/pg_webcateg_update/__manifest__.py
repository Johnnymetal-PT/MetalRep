# pg_webcateg_update/__manifest__.py
{
    "name": "PG Website Category XLSX Import",
    "version": "17.0.1.0.0",
    "author": "Parametro Global",
    "category": "Website",
    "summary": "Importa categorias eCommerce e POS para produtos a partir de XLSX (match por default_code).",
    "description": """
PG Website Category XLSX Import
===============================

a) Objetivo de negocio
----------------------
Atribuir em massa categorias de website (`product.public.category`) e/ou
categorias POS (`pos.category`) aos produtos a partir de uma folha XLSX,
fazendo match pelo `default_code` do produto. Pensado para refrescar a arvore
de categorias eCommerce quando o ficheiro mestre vem do exterior (PIM, ERP
secundario, etc.).

b) Pre-requisitos
-----------------
- Modulo `website_sale` (e implicitamente POS se for usar categorias POS).
- `openpyxl` instalado no servidor (importacao Python).
- Ficheiro XLSX com pelo menos as colunas:
  - default_code (configuravel via wizard)
  - website_categories (configuravel - pode passar a public_categ_ids)
  - pos_categ_ids (configuravel)
- O cabecalho pode estar em qualquer linha das 50 primeiras; o wizard procura
  o primeiro cabecalho que contenha todas as colunas necessarias.
- Permissoes para criar `product.public.category` e/ou `pos.category` se a
  opcao "Create missing categories" estiver ativa.

c) Como funciona
----------------
- `models/import_public_categories_wizard.py` define
  `import.public.categories.wizard` (TransientModel):
  - Upload `file_data` (XLSX) e nome.
  - Opcoes:
    - `do_website_categories` / `do_pos_categories` - escolher que arvore
      atualizar.
    - `website_id` - opcional. Se o modelo de categoria suportar `website_id`,
      restringe e cria sob esse website.
    - `only_active_products` - ignora produtos arquivados.
    - `create_missing_categories` - cria caminhos hierarquicos em falta.
    - `replace_categories` - se True, substitui o conjunto; se False, agrega.
  - Caminhos hierarquicos:
    - Separador `,` entre paths.
    - Separador ` / ` entre niveis dentro de um path.
    - Antes de pesquisar, normaliza espacos e trims.
    - Tenta match exato em `complete_name`; senao percorre por segmentos.
  - Devolve uma `display_notification` com totais (produtos nao encontrados,
    categorias atualizadas/criadas, etc.).
- `wizard/import_wizard_views.xml`: vista form + menu "Import Categories (XLSX)"
  sob `base.menu_custom`.

d) Passo a passo de utilizacao
------------------------------
1. Preparar XLSX com cabecalho contendo (no minimo):
   - `default_code`
   - `website_categories` (ou nome configurado)
   - `pos_categ_ids` (apenas se for usar POS)
2. No menu Configuracao / Import Categories (XLSX), abrir o wizard.
3. Carregar o ficheiro e escolher:
   - Atualizar website? POS? Ambos?
   - Substituir ou agregar.
   - Criar categorias em falta?
4. Clicar "Import" e ler a notificacao com o resumo.
5. Validar 1-2 produtos para confirmar a hierarquia.

e) Exemplo pratico
------------------
- Linha do XLSX:
  - default_code = "CAD-001"
  - website_categories = "Produtos Kave,Todas / Moveis / Sofas"
- Resultado:
  - Categoria "Produtos Kave" (cria se nao existir, ao nivel topo).
  - Categoria "Todas / Moveis / Sofas" (cria a hierarquia toda se necessario).
  - O template CAD-001 fica com `public_categ_ids` = essas duas categorias
    (substituicao ou agregacao consoante a opcao).

f) FAQ / Resolucao de problemas
-------------------------------
- "Erro: Could not find header row containing required columns":
  O nome das colunas no XLSX nao bate com o configurado. Editar o cabecalho
  ou ajustar os campos `Column for default_code`, `Website categories column`
  e `POS categories column` no wizard.
- "Erro: openpyxl is not installed on the server":
  Instalar `openpyxl` no Python do Odoo (`pip install openpyxl`).
- "Notificacao com 'Products not found' alto":
  Confirmar se os `default_code` no XLSX correspondem aos do Odoo. Espacos
  finais e prefixos sao silenciosamente removidos pelo `_norm`, mas case
  matters (compara exato).
- "Categorias nao sao criadas":
  Desativar `create_missing_categories` faz com que o wizard ignore caminhos
  inexistentes. Reativar e correr novamente.

g) Pontos de atencao
--------------------
- Substituicao usa `[(6, 0, ids)]`; agregacao usa `[(4, id)]`. Substituir
  remove categorias previas que nao apareciam no XLSX.
- Para POS, o codigo aceita uma coluna com paths hierarquicos mas a categoria
  POS standard nao tem `complete_name`; o match passa a ser por nome+pai.
- O modulo le e escreve com `sudo()` para evitar bloqueios de permissao;
  controlar quem tem acesso ao menu.
- O cabecalho e detetado nas primeiras 50 linhas; ficheiros com metadados em
  cima ate ao cabecalho funcionam.
    """,
    "depends": ["website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/import_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
