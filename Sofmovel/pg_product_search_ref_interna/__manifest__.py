{
    'name': 'PG Product Search Ref Interna',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Permite pesquisar produtos por `x_studio_referncia_interna` (alem de name e default_code).',
    'description': """
PG Product Search Ref Interna
=============================

a) Objetivo de negocio
----------------------
Em listas e campos Many2one de `product.product`, permitir aos utilizadores
encontrar produtos a partir do campo Studio `x_studio_referncia_interna`,
nao apenas pelo `name` ou pelo `default_code` standard. Tambem ajusta o
`display_name` para mostrar o codigo em prefixo `[<ref>] <nome>`.

NOTA: o `summary` no manifest original dizia "Add fields to cut the carpet and
sell by m2" - era copy/paste incorreto. O modulo nao tem relacao com m2.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `sale`.
- Campo Studio `x_studio_referncia_interna` (Char) em `product.product`.
  - O campo e geralmente provisionado por `pg_volumes_shipping` (ver
    `models/product_volume_template.py`) ou pelos imports
    (`pg_custom_product_import_extension*`).

c) Como funciona
----------------
- `models/product_product.py`:
  - `name_search`:
    - Constroi dominio com `OR` sobre `name`, `default_code` e
      `x_studio_referncia_interna`, com `operator` (default `ilike`) e
      junta com `args` recebidos.
    - Devolve `name_get()` do resultado.
  - `name_get`:
    - Para cada produto: usa `default_code` ou
      `x_studio_referncia_interna` como referencia.
    - Display name = `[<ref>] <name>` se houver ref; senao apenas `<name>`
      (ou "-" se nao houver).

d) Passo a passo de utilizacao
------------------------------
1. Instalar (ou atualizar) o modulo.
2. Em qualquer campo Many2one para `product.product` (linhas de SO, PO,
   POS - este via [[pg_pos_search_ref_interna]]) escrever a referencia
   interna do produto - aparece como sugestao.
3. Confirmar que o display name vem com `[<ref>] <nome>`.

e) Exemplo pratico
------------------
- Produto:
  - name = "Sofa Lisboa"
  - default_code = ""
  - x_studio_referncia_interna = "SOF-001"
- Pesquisa por "SOF": devolve o produto.
- Display name nos selects: "[SOF-001] Sofa Lisboa".

f) FAQ / Resolucao de problemas
-------------------------------
- "A pesquisa por referencia nao funciona":
  Verificar se o campo Studio `x_studio_referncia_interna` existe e esta
  preenchido. O modulo nao cria o campo.
- "O display name nao mostra a referencia":
  Confirmar que o produto tem default_code ou x_studio_referncia_interna
  preenchidos. Se ambos estiverem vazios, mostra apenas o nome.
- "Nao quero o prefixo [..]":
  Editar `name_get` em `models/product_product.py`. O comportamento foi
  escolhido para ficar igual ao standard Odoo (que ja mostra prefixo).

g) Pontos de atencao
--------------------
- O override de `name_search` substitui o standard - se outro modulo a
  estender depois (mesma instancia), garantir ordem de carga.
- A escrita do `name_get` repete o standard mas com prioridade ao
  `default_code` antes do Studio.
- A POS tem o seu modulo separado [[pg_pos_search_ref_interna]] porque a
  pesquisa em POS nao passa por `name_search` mas por uma string de pesquisa
  pre-computada (`_product_search_string`).
    """,
    'depends': ['base', 'product', 'sale'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
