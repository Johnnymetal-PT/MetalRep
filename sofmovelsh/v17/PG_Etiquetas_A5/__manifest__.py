{
    'name': 'PG Etiquetas A5',
    'version': '1.0',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'summary': 'Imprime etiquetas A5, 5x8 e ZPL para produtos e rececoes (com IoT Box para ZPL).',
    'description': """
PG Etiquetas A5
===============

a) Objetivo de negocio
----------------------
Centralizar a impressao de etiquetas de produto em multiplos formatos (A5, 5x8
e ZPL) a partir do produto ou da rececao de stock. Para ZPL, suporta enviar
diretamente a uma IoT Box configurada. O objetivo e que cada produto tenha
declarado o seu tipo de etiqueta (`print_label_type`) e que, na rececao, o
operador possa imprimir em lote as etiquetas corretas conforme o tipo de cada
linha.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `stock`, `iot`.
- Python: `PyPDF2` instalado no servidor Odoo (para fundir os PDFs A5/5x8).
- Relatorios Studio existentes (IDs hardcoded em `models/tag_a5.py`):
  - A5  - "studio_customization.studio_report_docume_6dda9565-82b4-45bc-ba88-b0a65488eb95"
  - 5x8 - "studio_customization.studio_report_docume_494c29ed-77e4-466a-adf4-30274ce43580"
  - ZPL - "studio_customization.studio_report_docume_ee312668-34d8-4791-bf96-c8381ed8abac"
  - Etiqueta A5 a partir do template - "studio_customization.studio_report_docume_52767c0b-fd5e-41c6-9934-c0875e4b4227"
  - Etiqueta A5 a partir da variante - "studio_customization.studio_report_docume_4d3ac47d-eb3c-4172-873a-69ef757664d3"
- IoT Box configurada e visivel em `iot.box` (necessario para impressao ZPL via
  driver nativo).

c) Como funciona
----------------
- `models/tag_a5.py`:
  - `product.template` ganha `print_label_type` (A5/5x8/ZPL; default ZPL) e o
    botao `action_print_a5_studio_label`, que invoca o relatorio Studio
    correspondente ao template.
  - `product.product` recebe o mesmo `print_label_type` (related store) e o
    botao `action_print_a5_studio_label` para a variante.
  - `stock.picking` recebe:
    - `has_zpl_labels` (compute) que diz se existem moves com etiquetas ZPL.
    - `_get_label_moves` que devolve as moves ativas; usa fallback para
      `move_line_ids` ou `move_ids_without_package` para suportar pickings em
      draft sem moves ainda materializadas.
    - `_get_move_label_qty` que escolhe entre `product_uom_qty`,
      `quantity_done` e `reserved_availability` para decidir a quantidade a
      imprimir.
    - `action_open_zpl_printer` que abre o wizard `choose.iot.printer.wizard`.
    - `action_print_received_labels` que junta A5 e 5x8 num so PDF (via
      `PdfMerger`), cria um `ir.attachment` e devolve uma `ir.actions.act_url`
      para descarregar.
- `wizards/choose_iot_printer.py`:
  - `choose.iot.printer.wizard` recebe a `iot.box` escolhida pelo utilizador
    e chama o relatorio ZPL com `iot_device_id` no contexto, deixando o driver
    nativo do Odoo encaminhar para a impressora.

d) Passo a passo de utilizacao
------------------------------
1. No cadastro do produto definir `print_label_type` (A5, 5x8 ou ZPL).
2. Para imprimir a etiqueta de um produto isolado, abrir o produto e usar o
   botao de imprimir A5 (relatorio Studio).
3. Numa rececao de stock (stock.picking de entrada):
   - Confirmar/rececionar como habitualmente.
   - Para etiquetas A5/5x8, clicar em "Imprimir etiquetas recebidas". O sistema
     junta todos os tipos em PDF unico e oferece-o para download.
   - Se houver linhas ZPL, clicar em "Escolher Impressora ZPL"; selecionar a
     IoT Box configurada e confirmar. O Odoo envia o relatorio ZPL para a IoT.

e) Exemplo pratico
------------------
- Rececao com 3 linhas:
  - Produto A (10 un, tipo A5)
  - Produto B (5 un, tipo 5x8)
  - Produto C (20 un, tipo ZPL)
- "Imprimir etiquetas recebidas" devolve PDF com 10 A5 + 5 5x8 fundidas.
- "Escolher Impressora ZPL" -> escolher IoT da Receção -> envia 20 etiquetas
  ZPL via driver IoT.

f) FAQ / Resolucao de problemas
-------------------------------
- "Erro: Nao foram encontradas etiquetas A5/8x5":
  Significa que nenhuma das moves tem produto com `print_label_type` A5 ou 5x8
  e quantidade > 0. Verificar o tipo de etiqueta nos produtos.
- "Erro: Nao foram encontradas etiquetas ZPL":
  Mesmo problema, mas para ZPL. Confirmar se a coluna de tipo de etiqueta nos
  produtos esta a "ZPL".
- "Erro: Relatorio de etiquetas ZPL nao encontrado":
  O ID Studio do relatorio mudou. Repor os IDs Studio hardcoded em
  `models/tag_a5.py` e `wizards/choose_iot_printer.py`.
- "A impressao ZPL nao sai mesmo escolhendo a IoT":
  Validar que `iot.box` esta online e que a impressora ZPL esta detetada por
  ela; o `iot_device_id` precisa apontar para um device valido.

g) Pontos de atencao
--------------------
- Existem IDs Studio fixos em codigo (`studio_report_docume_...`). Qualquer
  recriacao do relatorio Studio quebra a impressao; sao o ponto sensivel deste
  modulo.
- A fusao de PDFs depende de `PyPDF2`; sem essa biblioteca o
  `action_print_received_labels` rebenta antes mesmo de criar o anexo.
- Em pickings novos sem moves materializadas, o codigo cai no fallback de
  `move_line_ids`/`move_ids_without_package`. Validar localmente se a
  rececao em causa esta em estado coerente antes de imprimir.
- O modulo declara dependencia em `iot`; em ambientes sem `iot` instalado nao
  e instalavel.

[FACTO OBSERVADO] suporta tres formatos (A5, 5x8, ZPL) e respetivos pontos de
entrada (template, variante e picking).
[INFERENCIA] [[pg_zpl_tags_sofmovel]] e uma abordagem anterior para ZPL
(impressao por `subprocess lp` numa impressora chamada "Etiquetas"). Validar se
ainda esta em producao ou se deve ser arquivada.
    """,
    'author': 'Parametro Global',
    'website': 'http://www.parametroglobal.pt',
    'depends': ['base', 'product', 'stock', 'iot'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_selector.xml',
        'views/stock_picking_button.xml',
        'views/wizard.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
