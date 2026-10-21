{
    'name': 'PG Variant Upload with Custom Attributes',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Importa produtos com atributos e variantes a partir de Excel e cria atributos custom textuais.',
    'description': """
PG Variant Upload with Custom Attributes
========================================

a) Objetivo de negocio
----------------------
Carregar em massa, a partir de um Excel, atributos e variantes de produto.
- Linhas 1 e 2 do Excel definem o cabecalho de duas niveis:
  - Linha 1 (com celulas mescladas): categoria do atributo (ex. "Cor",
    "Tamanho").
  - Linha 2: variantes/valores (ex. "Vermelho", "Azul", "S", "M", "L").
- Da linha 3 em diante: 1 produto por linha; cada celula tem o `price_extra`
  ou um texto descritivo para a combinacao atributo+variante.
Quando a celula contem texto (nao numerico), o modulo cria um
`custom.product.attribute` (atributo textual livre, fora do sistema de
variantes standard) em vez de uma `product.attribute.value`.

b) Pre-requisitos
-----------------
- Modulos: `product`, `website_sale`.
- Bibliotecas Python: `pandas`, `openpyxl`.
- Excel com a estrutura descrita acima (2 linhas de cabecalho).

c) Como funciona
----------------
- `models/custom_attribute.py`:
  - Define `custom.product.attribute` (Char name, Many2one product, Text
    description, sequence). E o "atributo textual" que substitui a
    `product.attribute.value` quando o XLSX tem texto na celula.
  - Define `custom.product.attribute.value` (atualmente nao usado pelo
    fluxo). [PONTO POR VALIDAR] se e para manter.
- `models/product_template.py`: One2many `custom_attribute_ids` em
  `product.template`.
- `models/product_import_wizard.py`:
  - `product.import.wizard` (Binary file + filename) chama
    `product.import.import_file` passando o ficheiro tempfile.
  - `product.import.import_file`:
    1. Le primeira folha; constroi `attr_variant_map` por coluna a partir das
       linhas 1 e 2.
    2. Para cada (atributo, variante) cria `product.attribute` e
       `product.attribute.value` se nao existirem.
    3. Apaga TODOS os `custom.product.attribute` existentes ("limpa" antes de
       reescrever). [Ponto sensivel: ver FAQ.]
    4. Para cada produto (linha >= 3): se nao existir, cria `product.template`
       (publicado, type='product'); se a celula for texto, cria um custom
       attribute; se for numerica, cria/atualiza a attribute line e regista
       `price_extra`.
- `wizards/product_import_wizard.py`: codigo antigo comentado (referencia).

d) Passo a passo de utilizacao
------------------------------
1. Preparar Excel com 2 linhas de cabecalho (categorias mescladas + variantes).
2. Abrir o wizard a partir do menu/vista que invoca `product.import.wizard`.
3. Carregar o ficheiro e nome.
4. Aceitar; o wizard chama `product.import.import_file` e processa.

e) Exemplo pratico
------------------
Estrutura do XLSX:

    | Atributos | Cor             | Cor             | Tamanho |
    | Variantes | Vermelho        | Azul            | M       |
    | Cadeira X | 5.00            | "Tecido especial"| 0      |

- Sao criados: atributo "Cor" com valores "Vermelho" e "Azul"; atributo
  "Tamanho" com valor "M".
- "Cadeira X" recebe attribute line para "Cor" com Vermelho (price_extra=5)
  e attribute line para "Tamanho" com M (price_extra=0).
- Para a celula "Tecido especial", e criado um `custom.product.attribute`
  (texto), nao uma variant value.

f) FAQ / Resolucao de problemas
-------------------------------
- "Custom attributes desaparecem ao importar":
  O wizard apaga TODOS os `custom.product.attribute` antes de processar. Se
  precisar de manter custom attributes nao incluidos no XLSX, NAO correr o
  wizard - ou comentar a linha `unlink()` correspondente.
- "Variantes nao aparecem nos produtos":
  Confirmar que as celulas numericas estao com numeros (e nao strings). O
  wizard distingue: numerico = variant value + attribute line; texto =
  custom attribute.
- "Erro ao criar produto novo":
  O wizard cria `product.template` com `type='product'` e
  `website_published=True`. Se houver constraints de IVA ou de empresa, ler
  o erro detalhado.

g) Pontos de atencao
--------------------
- Convive com [[pg_custom_product_import_extension_2]] (que tambem usa
  `custom.product.attribute`).
- O wizard nao tem savepoint nem retries; em caso de falha a transacao
  pode abortar.
- Diretorio `.idea/` (PyCharm) esta presente; pode ser limpo do repositorio.

[FACTO OBSERVADO] `wizards/product_import_wizard.py` contem apenas codigo
comentado, mantido como referencia.
    """,
    'depends': ['website_sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
