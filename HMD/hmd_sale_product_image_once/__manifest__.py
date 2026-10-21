{
    "name": "HMD Sale Product Image Once",
    "version": "18.0.1.0.0",
    "summary": "Preenche a imagem da linha de venda uma vez a partir do produto e respeita edicoes manuais.",
    "author": "HMD / Parametro Global",
    "license": "LGPL-3",
    "depends": ["sale_management"],
    "data": [],
    "description": """
HMD Sale Product Image Once (HMD)
=================================

a) Objetivo de negocio
----------------------
A HMD tem em Studio um campo `x_studio_imagem_do_produto` em cada
linha de venda que serve para personalizar a imagem por linha (ex.:
imagem do moinho do cliente, render com cor especifica). O standard
nao copia nada para esse campo; o comercial tinha de arrastar a
imagem cada vez. Este modulo:
  - copia automaticamente a imagem do produto para a linha quando o
    produto e definido pela primeira vez;
  - se o utilizador editar manualmente, marca a linha com o flag
    `hmd_sale_product_image_manual=True` e a partir dai NUNCA mais
    sobrepoe (nem trocar de produto retira a imagem custom).

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `sale_management`.
- Campo Studio `sale.order.line.x_studio_imagem_do_produto`
  (Binary/Image) - se renomeado, alterar a constante
  `_sale_line_image_field`.

c) Como funciona (tecnico)
--------------------------
1. `sale.order.line` (`models/sale_order_line.py`):
   - `_sale_line_image_field = 'x_studio_imagem_do_produto'`
     (constante; ponto unico se for renomear).
   - `_product_image_fields = ('image_1920', '1024', ...)` - ordem
     de fallback ao buscar imagem do produto.
   - `hmd_sale_product_image_manual` (Boolean, default False): flag
     que indica que o utilizador mexeu manualmente.

2. `_get_default_sale_line_image`: tenta `product.image_1920`,
   depois `image_1024`, ..., depois o template. Devolve o primeiro
   nao-vazio.

3. `_is_manual_sale_line_image`: compara o valor atual da imagem
   com o default. Se diferente -> e manual.

4. `_set_default_sale_line_image`: pega na imagem do produto e
   poe na linha SE o flag manual nao estiver ativo.

5. Hooks:
   - `_onchange_product_id_set_sale_line_image`: ao escolher produto
     na UI, se nao houver edicao manual previa, preenche a imagem.
   - `_onchange_sale_line_image_mark_manual`: ao editar a imagem,
     verifica se difere do default e marca o flag.
   - `create`: aplica defaults e sincroniza o flag.
   - `write`: especial - se vals tem image_field mas nao
     manual_field, percorre linhas e SE estiver manual ignora a
     alteracao em massa (preserva a manual edit).

d) Passo a passo de utilizacao
------------------------------
1. Garantir que `x_studio_imagem_do_produto` existe em Studio.
2. Instalar `hmd_sale_product_image_once`.
3. Vendas > Orcamentos > criar.
4. Adicionar linha com produto - a imagem do produto aparece
   automaticamente.
5. Para custom: clicar no campo imagem e mudar - a partir desse
   momento, mudar de produto NAO sobrepoe.
6. Para voltar ao default: limpar o campo (`x_studio_imagem_do_produto
   = False`); o sync compara com default e marca o flag como
   "alinhado".

e) Exemplo pratico
------------------
Produto "Sofa Lara" tem `image_1920` = foto generica.
SO S010, linha 1: adicionar produto -> imagem automaticamente igual
a foto generica. Linha 2 idem.

Em L1, o comercial carrega uma foto personalizada do cliente:
  - flag manual = True.
  - Mudar o produto para "Sofa Outra" NAO troca a imagem.

Em L2, intacta: mudar produto -> a imagem segue o novo produto.

f) FAQ / Resolucao de problemas
-------------------------------
P: A imagem nao aparece automaticamente. Porque?
R: O produto pode nao ter `image_1920` nem image (verificar). Ou o
   campo Studio nao se chama `x_studio_imagem_do_produto`.

P: Carreguei imagem manual mas continua a ser sobrescrita.
R: Verificar o valor do `hmd_sale_product_image_manual`. Se False,
   o `_onchange_sale_line_image_mark_manual` nao correu (a UI nao
   disparou). Pode ser preciso forcar via api ou reabrir a linha.

P: Como resetar para o default automatico?
R: Limpar o campo (`x_studio_imagem_do_produto = False`); o sync
   recalcula. Como o valor da imagem fica igual ao default (False vs
   False), o flag fica False e a partir dai re-segue o produto.

g) Pontos de atencao / avisos
-----------------------------
- DEPENDENCIA STUDIO `x_studio_imagem_do_produto`.
- O `write` deteta a flag manual ao nivel de cada linha (loop) -
  custo O(n) mas n e tipicamente pequeno em UI.
- A flag `hmd_sale_product_image_manual` e tecnica - manter
  `readonly` nas views custom para nao confundir o utilizador.
""",
    "installable": True,
    "application": False,
}
