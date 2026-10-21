# -*- coding: utf-8 -*-
{
    'name': 'PG Product Upload with Custom Attributes',
    'version': '17.0.1.0.0',
    'category': 'Inventory',
    'summary': 'Importa produtos e variantes de um Excel (formato Piccolo): primeira linha = nome do atributo (merged cells), segunda linha = nome da variante, colunas seguintes = price_extra; cria/atualiza product.template + product.attribute + product.attribute.value + product.template.attribute.line.',
    'author': 'Parametro Global',
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_import_wizard_view.xml',
    ],
    'description': """
PG Product Upload
=================

a) Objetivo de negocio
----------------------
Carregar em batch os produtos do catalogo Piccolo a partir de um
Excel: definicao de atributos (cor, tecido, tamanho, etc.), variantes
e respetivos ``price_extra``. Tambem alimenta os "Atributos
Personalizados" (descricoes textuais por atributo no produto).

b) Pre-requisitos
-----------------
- Modulo standard ``product``.
- Bibliotecas Python: ``pandas`` e ``openpyxl`` (le ``.xlsx``).
- Excel com a estrutura **EXATA**:
  - **Linha 1**: nome do atributo (cells horizontais merged sobre
    as variantes desse atributo). ``Atributos`` e ``Variantes``
    sao palavras-chave reservadas.
  - **Linha 2**: nome da variante por coluna.
  - **Linhas 3+**: nome do produto na coluna 0; price_extra ou
    descricao textual nas colunas seguintes.

c) Como funciona
----------------
- ``models/custom_attribute.py`` define dois modelos novos:
  - ``custom.product.attribute`` (atributo textual descritivo do
    produto, com sequence).
  - ``custom.product.attribute.value`` (valor de cada variante).
- ``models/product_template.py`` acrescenta ``custom_attribute_ids``
  ao template para os exibir/editar.
- ``models/product_import_wizard.py``:
  - ``product.import.wizard`` recebe ficheiro -> escreve em
    ``tempfile`` -> chama ``product.import.import_file``.
  - ``product.import.import_file`` (TransientModel):
    1. ``df.iloc[0]`` -> nomes de atributo (com ``ffill`` para
       resolver merged cells).
    2. ``df.iloc[1]`` -> nomes de variante por coluna.
    3. Cria ``product.attribute`` (com ``display_type=select`` e
       ``unavailable_value_view_type=hide``) e ``.value`` se nao
       existirem.
    4. Para cada linha de produto (a partir da 3):
       - Cria ou encontra ``product.template`` (e variant).
       - Substitui ``custom.product.attribute`` por linha (unlink
         do existente para o produto).
       - Para cada coluna: se valor numerico -> trata como
         ``price_extra`` do PTAV. Se valor nao numerico -> cria
         ``custom.product.attribute`` (descricao textual).
- ``wizards/product_import_wizard.py`` esta inteiramente comentado
  (versao antiga deixada por documentacao).

d) Passo a passo de utilizacao
------------------------------
1. Instalar (garantir ``pandas`` + ``openpyxl`` no servidor).
2. Preparar Excel:
   - Linha 1: "Atributos" "Variantes" "TECIDO" "TECIDO" ... (merge
     cells por atributo).
   - Linha 2: "" "" "Linho Bege" "Linho Castanho" ...
   - Linha 3+: "Cadeira X" "Standard" 0 10 ...
3. Inventario > Wizard "Importar Produtos" > carregar ficheiro.
4. Confirmar - os produtos sao criados/atualizados.

e) Exemplo pratico
------------------
Excel com:
- Linha 1: Atributos | Variantes | TECIDO | TECIDO | ACABAMENTO
- Linha 2: (vazio) | (vazio) | Linho Bege | Linho Castanho | Verniz
- Linha 3: Cadeira X | Standard | 0 | 10 | 15

Cria:
- ``product.attribute`` "TECIDO" com valores "Linho Bege" e "Linho
  Castanho".
- ``product.attribute`` "ACABAMENTO" com valor "Verniz".
- ``product.template`` "Cadeira X" com atributos TECIDO e ACABAMENTO.
- PTAV "Linho Bege" com ``price_extra = 0``, "Linho Castanho" com
  ``price_extra = 10``, "Verniz" com ``price_extra = 15``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Atributos misturados"* -> as cells de linha 1 nao estao merged;
  ``ffill`` so propaga ``NaN`` se a primeira nao estiver vazia.
- *"Variantes nao aparecem no produto"* -> linha do produto tem
  valores numericos em colunas cujo atributo nao foi criado primeiro.
- *"price_extra nao atualiza"* -> ja existia PTAV; o codigo
  pesquisa por ``product_attribute_value_id`` apenas (sem template),
  o que para variantes partilhadas pode escrever no PTAV errado.
  Validar manualmente.
- *"Pandas FutureWarning"* -> ``fillna(method='ffill')`` deprecated
  em pandas 2.x; usar ``ffill()`` direto numa proxima iteracao.

g) Pontos de atencao / avisos
-----------------------------
- **Importante**: re-importacao **APAGA** os
  ``custom.product.attribute`` dos produtos da importacao
  (``unlink`` na linha 109 de ``models/product_import_wizard.py``).
  As variantes/atributos standard nao sao apagadas, mas os
  textuais sim. Backup antes de re-import.
- O wizard cria ``product.template`` se nao existir, com
  ``website_published=True`` - novos produtos ficam publicos.
- Match por nome **exato** (case-sensitive); typos no Excel viram
  produtos novos.
- Logica de update de PTAV procura por ``product_attribute_value_id``
  sem filtrar por template - se um valor for partilhado por varios
  templates, escreve no primeiro PTAV encontrado.
- O ficheiro ``wizards/product_import_wizard.py`` esta TODO em
  comentario (versao antiga). Manter por referencia ou remover na
  proxima limpeza.
""",
    'installable': True,
    'application': False,
}
