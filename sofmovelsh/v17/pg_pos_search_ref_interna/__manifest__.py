{
    'name': 'PG POS Search Ref Interna',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Point of Sale',
    'summary': 'Permite pesquisar produtos no POS pela referencia interna Studio (x_studio_referncia_interna).',
    'description': """
PG POS Search Ref Interna
=========================

a) Objetivo de negocio
----------------------
Permitir aos operadores de POS pesquisar produtos pela referencia interna
Studio (`x_studio_referncia_interna`), nao so pelo nome, codigo de barras
ou `default_code`. E o equivalente em POS do que
[[pg_product_search_ref_interna]] faz no backoffice.

b) Pre-requisitos
-----------------
- Modulo standard `point_of_sale`.
- Campo Studio `x_studio_referncia_interna` em `product.product` (mesmo
  campo usado pelo [[pg_volumes_shipping]] e pelos wizards de importacao).
- Sessao POS recarregada apos instalar o modulo (para os assets JS serem
  servidos).

c) Como funciona
----------------
- `models/pos_session.py`:
  - Override de `_loader_params_product_product` para incluir
    `x_studio_referncia_interna` na lista de campos carregados pelo POS.
- `static/src/js/product_search.js`:
  - Patch a `PosDB.prototype._product_search_string`:
    - Chama o original e anexa `|<x_studio_referncia_interna>` no fim,
      garantindo que a referencia entra no string usado pela pesquisa
      interna do POS.
  - Mantem a quebra de linha standard do Odoo (cada produto ocupa uma
    linha no indice de pesquisa).

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo e reiniciar a sessao POS.
2. No ecra do POS, na caixa de pesquisa de produtos, escrever a referencia
   Studio. O produto deve aparecer.
3. Confirmar que continua a funcionar pesquisar por nome e por barcode.

e) Exemplo pratico
------------------
- Produto:
  - name = "Cadeira Office"
  - x_studio_referncia_interna = "CAD-OFF-001"
- No POS: escrever "CAD-OFF" mostra o produto.

f) FAQ / Resolucao de problemas
-------------------------------
- "O patch nao aparece estar a funcionar":
  A sessao POS le os assets uma so vez. Sair da sessao, limpar cache do
  browser (Ctrl+Shift+R) e voltar a entrar.
- "O campo nao chega ao POS":
  O override de `_loader_params_product_product` adiciona o campo a lista
  carregada. Se outro modulo a estender depois e nao incluir
  `x_studio_referncia_interna`, validar a ordem de carga.
- "Display name no POS continua sem prefixo":
  Este modulo so altera a string de pesquisa, nao o display name. Para
  display name customizado e preciso outro patch.

g) Pontos de atencao
--------------------
- E uma extensao JS a um metodo privado do POS (`_product_search_string`).
  Em futuras versoes Odoo o metodo pode mudar de nome ou de assinatura -
  validar apos cada upgrade.
- Carregado pelo bundle `point_of_sale._assets_pos`.
    """,
    'depends': ['point_of_sale'],
    'data': [],
    'assets': {
        'point_of_sale._assets_pos': [
            'pg_pos_search_ref_interna/static/src/js/product_search.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
