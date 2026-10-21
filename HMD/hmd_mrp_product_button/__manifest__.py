# -*- coding: utf-8 -*-
{
    'name': 'HMD MRP Product Button',
    'version': '18.0.1.0.0',
    'summary': 'Botao "Ver Produto" nas linhas de BoM e da Ordem de Producao.',
    'description': """
HMD MRP Product Button
======================

a) Objetivo de negocio
----------------------
Em formulario de BoM ou de Ordem de Producao, os componentes aparecem
como uma lista compacta - clicar num componente nao abre o produto, e
abrir o produto exige sair, navegar e procurar. Este modulo adiciona
um link "Ver Produto" em cada linha de BoM, de `move_raw_ids` e de
`move_finished_ids` que abre diretamente o `product.template` da
linha.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `mrp` instalado.

c) Como funciona (tecnico)
--------------------------
Adiciona `action_view_product_template()` a:
- `mrp.bom.line`: usado nas linhas da BoM.
- `stock.move`: usado nas linhas materia-prima
  (`move_raw_ids`) e produto acabado (`move_finished_ids`) da MO.
Em ambos, devolve `act_window` apontando para o template
(`product.template`) do produto da linha.

As views (`views/mrp_bom_line_views.xml`) injetam botoes "Ver Produto"
(class `oe_link`, com `attrs` invisivel quando `product_id` esta
vazio) antes da coluna `product_id`.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `hmd_mrp_product_button`.
2. Abrir uma BoM (Fabrico > Lista de materiais).
3. Em cada linha aparece o link "Ver Produto" no inicio.
4. Idem ao abrir uma Ordem de Producao (`mrp.production`) - secao
   "Materia-prima" e "Acabados".
5. Clicar abre o template do produto correspondente.

e) Exemplo pratico
------------------
BoM do "Sofa Lara" lista o componente "Tecido cima". Operador clica
"Ver Produto" -> abre o template do produto "Tecido cima" para
verificar atributos/imagens/notas.

f) FAQ / Resolucao de problemas
-------------------------------
P: O link nao aparece. Porque?
R: A linha pode nao ter `product_id` definido (o `attrs` esconde
   nesse caso). Ou a view custom foi mexida sem manter o xpath.

P: Clico mas nao abre nada. Porque?
R: O metodo devolve `False` se nao houver product_id ou template.
   Verificar que a linha tem produto associado.

g) Pontos de atencao / avisos
-----------------------------
- Sem dependencias custom. Compativel com pg_tecidos
  (`mrp.bom.line._compute_product_template_attachment_ids` la nao
  conflitua com este).
- O `target='current'` substitui a vista atual - se for preferivel
  abrir em janela nova, alterar para `'new'`.
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['mrp'],
    'data': [
        'views/mrp_bom_line_views.xml',
    ],
    'installable': True,
    'application': False,
}
