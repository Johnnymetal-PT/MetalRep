{
    'name': 'PG Packing List Personalizado',
    'version': '18.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Packing list HMD: volumes, dimensoes, peso e cubicagem em produto, venda e entrega.',
    'description': """
PG Packing List Personalizado (HMD)
===================================

a) Objetivo de negocio
----------------------
A HMD precisa de gerir packing list sem manter folhas Excel paralelas:
saber por produto quantos volumes leva, qual o peso e qual a cubicagem
em m3, e propagar esses totais para venda e entrega (`stock.picking`).
A operacao logistica calcula o transporte com base na cubicagem, e o
financeiro precisa do peso para a guia de transporte. Este modulo
centraliza tudo no produto e calcula automaticamente.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos standard: `product`, `stock`, `sale`, `mail`, `base`.
- Sem dependencia de Studio, mas as views adicionam aba ao formulario
  standard de `product.template`.

c) Como funciona (tecnico)
--------------------------
Adiciona campos a tres modelos e introduz um wizard transacional:

1. `product.template` (`models/product_template.py`):
   - `packing_volumes` (Float): numero de volumes do produto (max 6,
     constraint em `_check_volumes_range`).
   - `packing_weight` (Float): peso unitario em kg.
   - `packing_cubicagem` (Float, computed/stored): cubicagem total em
     m3 calculada a partir das dimensoes (C x A x L) dos volumes 1..N
     em que N = floor(min(6, packing_volumes)).
   - 18 campos C/A/L para volumes 1 a 6.
   - As views (`views/product_template_views.xml`) escondem volumes 2
     a 6 progressivamente conforme o `packing_volumes` cresce
     (`invisible="packing_volumes <= 1.49"`, etc.) - o limiar 1.49 e
     intencional para que `packing_volumes = 1.5` ja mostre o volume 2.

2. `sale.order` + `sale.order.line` (`models/sale_order.py`):
   - Totais ao nivel da venda (`total_packing_*`) e por linha
     (`line_packing_*`), todos computed e armazenados.
   - `_sync_move_packing` propaga os valores da linha de venda para o
     `stock.move` ligado (matching por `sale_line_id`). E chamado em
     `_compute_line_packing` e em `write()` quando algum dos campos de
     packing da linha muda - para manter sincronizada a operacao
     logistica quando o utilizador recalcula via wizard.
   - Botao "calculadora" (icon 🧮) por linha que abre o wizard com a
     linha de venda em contexto.

3. `stock.picking` + `stock.move` (`models/stock_picking.py`):
   - Totais a nivel de entrega (`total_packing_*`).
   - Campos por linha de movimento (`move_packing_*`) recalculados a
     partir do produto/qty. O wizard tambem escreve diretamente nestes
     campos quando o utilizador confirma.

4. Wizard `cubicagem.wizard` (`wizard/cubicagem_wizard.py`):
   - Aberto a partir de uma linha de venda ou de uma linha de stock.
   - Pre-preenche-se com `default_get` a partir do contexto.
   - Calcula a cubicagem em tempo real (computed).
   - "Peso Manual" (checkbox): se ativo, usa o valor introduzido;
     senao, calcula peso = `cubicagem_total * 80` (regra de negocio
     HMD: 80 kg/m3 medio, configurada hardcoded no metodo
     `action_calcular`).
   - Ao confirmar, escreve em `stock.move` e/ou em `sale.order.line` +
     re-sincroniza todos os `stock.move` ligados a essa linha de venda.

d) Passo a passo de utilizacao
------------------------------
Preencher packing num produto:
  1. Inventario > Artigos > abrir um produto > aba "Packing List".
  2. Preencher `Volumes` (ex.: 2). Imediatamente aparecem as dimensoes
     do volume 2.
  3. Preencher Comprimento, Altura, Largura de cada volume em metros.
  4. `Cubicagem` calcula automaticamente. Preencher `Peso (Kg)` se for
     constante; senao ficara a 0 e sera estimado pelo wizard.

Calcular numa linha de venda (overrides especificos do orcamento):
  1. Vendas > Orcamentos > abrir.
  2. Em cada linha aparecem `Volumes`, `Peso`, `Cubicagem` + botao 🧮.
  3. Clicar 🧮: o wizard abre ja preenchido com os valores do produto.
  4. Ajustar volumes/dimensoes (override transitorio) e premir Calcular.
     Os totais da venda e dos `stock.move` ligados sao atualizados.

Calcular numa entrega:
  1. Inventario > Transferencias > abrir uma entrega.
  2. Em cada linha de movimento aparece o icon 🧮 (oculto se a entrega
     ja esta em estado `done`).
  3. Mesmo fluxo do wizard.

e) Exemplo pratico
------------------
Produto "Sofa 3 lugares" tipicamente enviado em 2 volumes:
  - Volumes = 2
  - Vol 1: 2.10 x 0.85 x 0.95  -> 1.696 m3
  - Vol 2: 0.45 x 0.50 x 0.95  -> 0.214 m3
  - `packing_cubicagem` = 1.910 m3
  - `packing_weight` = 75 kg (preenchido manualmente)

Em venda com `product_uom_qty = 3`:
  - `line_packing_volumes` = 6
  - `line_packing_cubicagem` = 5.730 m3
  - `line_packing_weight` = 225 kg

No wizard, sem peso manual: peso estimado = 5.730 * 80 = 458.40 kg
(usado quando o cliente nao tem peso constante por produto). Com peso
manual: usa o valor introduzido.

f) FAQ / Resolucao de problemas
-------------------------------
P: Porque e que os volumes 2 a 6 nao aparecem na aba?
R: Os limiares de visibilidade sao 1.49, 2.49, 3.49, 4.49, 5.49. O
   valor minimo para o volume N aparecer e N-0.51. Isto e intencional
   para tolerar arredondamentos. Se preencher `Volumes = 2` o volume 2
   aparece. Para preencher dimensoes do volume 3 sem ter 3 volumes
   reais, subir o `Volumes` temporariamente.

P: O peso na linha de venda muda mas o `stock.move` nao reflete. Porque?
R: O sync acontece em `_compute_line_packing` e em `write()`. Se o
   `stock.move` ja existia antes do produto ter packing, executar uma
   recomputacao na linha de venda (alterar e voltar a por a quantidade)
   ou usar o wizard - este forca o write nos moves ligados.

P: A formula peso = cubicagem * 80 e generica. Posso ajustar?
R: Sim. Esta hardcoded em `wizard/cubicagem_wizard.py::action_calcular`
   (`peso_estimado = self.cubicagem_total * 80`). Se for preciso por
   categoria de produto, evoluir para um parametro `ir.config_parameter`
   ou um campo no produto. Por agora e fixo: 80 kg/m3.

P: Suporta mais de 6 volumes?
R: Nao. Limite duro em `_check_volumes_range` (`> 6` levanta
   `ValidationError`). Os campos so existem ate ao indice 6.

P: O wizard so abre na linha. Posso abrir geral na entrega?
R: Sim - existe `action_open_cubicagem_wizard` em `stock.picking`, mas
   nao tem botao no XML por defeito. Adicionar XML inherit se for util.

g) Pontos de atencao / avisos
-----------------------------
- HARDCODED: peso estimado = cubicagem * 80. Regra de negocio HMD,
  documentar antes de qualquer upgrade.
- Limiares de visibilidade `1.49`, `2.49`, ... funcionam com
  `packing_volumes` inteiro. Se alguem usar valores fracionarios
  (ex.: 2.3), o comportamento e ambiguo - o `range(int(min(6, ...)))`
  no compute usa a parte inteira, mas a UI ja mostraria o volume 3.
- `_compute_line_packing` chama `_sync_move_packing` dentro do loop.
  Se a venda tiver muitas linhas com muitos moves, o desempenho pode
  degradar - aceitavel no contexto HMD (volumes pequenos), mas
  monitorizar.
- `_check_dimensions_positive` usa `f-string` com `record._fields[...]`.
  Em locais onde o field tenha label traduzida, a label sai na lingua
  do utilizador, o que pode confundir testes automatizados.
- Em upgrade para Odoo 19, validar:
   - `move_ids_without_package` em `stock.picking` (campo standard);
   - hook do botao via `attrs` em vez de `invisible` declarativo - o
     `stock_picking_views.xml` mistura ambos.
""",
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'depends': ['base', 'product', 'stock', 'sale'],
    'data': [
        'views/product_template_views.xml',
        'views/stock_picking_views.xml',
        'views/sale_order_views.xml',
        'wizard/cubicagem_wizard_views.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
