# -*- coding: utf-8 -*-
{
    'name': 'PG ZPL TAGS 2',
    'version': '17.0.2.0.0',
    'summary': 'Imprime etiquetas ZPL para Zebra a partir de um stock.picking via wizard. Tres templates (Tecidos / J.Dias / Acabamento) selecionaveis no popup.',
    'description': """
PG ZPL TAGS 2
=============

a) Objetivo de negocio
----------------------
Imprimir etiquetas de identificacao para colar nos volumes a
expedir, com dados consistentes do picking (cliente, encomenda, ref
do cliente, cor, modelo) - direto numa impressora Zebra (raw ZPL).
Tres formatos: 'produtos' (Tecidos), 'jdias' (J.Dias) e
'acabamento' (Acabamento/Polimento).

b) Pre-requisitos
-----------------
- Modulo standard ``sale_stock``.
- Impressora Zebra (ou compativel) acessivel via CUPS, com a fila
  de impressao registada como ``ZEBRAP`` (HARDCODED no codigo - ver
  "Pontos de atencao").
- Biblioteca Python ``pycups`` instalada no servidor Odoo (``import
  cups``).
- Servidor Odoo com permissao de escrita em ``/tmp/`` (path
  ``/tmp/zpl_print_job2.zpl`` HARDCODED).
- Campos Studio no ``stock.picking`` e ``stock.move`` usados nos
  templates ZPL:
  - ``x_studio_cliente_1`` (Many2one res.partner)
  - ``x_studio_sale_order_name`` (Char)
  - ``x_studio_referncia_do_cliente_2`` (sic - typo de Studio)
  - ``x_studio_referncia_do_cliente`` (variante usada em jdias/acabamento)
  - ``x_studio_referncia_2``
  - ``stock.move.x_studio_cor``
  - ``stock.move.x_studio_volumes_3``

c) Como funciona
----------------
- ``models/zpl_tags.py``:
  - Acrescenta ``enable_zpl_printing2`` (bool) no ``stock.picking``.
  - ``action_open_zpl_wizard``: abre o wizard
    ``zpl.label.wizard`` em modal, passando o picking via context.
  - ``action_print_zpl2(label_size)``: itera ``move_ids_without_package``
    -> ``move_line_ids``, monta o ZPL com f-string interpolando
    campos Studio do picking e do move. Repete o codigo
    ``volume`` vezes (= ``move.x_studio_volumes_3``).
  - ``_send_to_printer2``: escreve ZPL em
    ``/tmp/zpl_print_job2.zpl``, abre conexao CUPS, valida que a
    impressora ``ZEBRAP`` existe e envia com flag ``raw=true``.

- ``wizard/zpl_tags_wizard.py`` (TransientModel ``zpl.label.wizard``):
  - Selection ``label_size`` com os 3 templates.
  - ``action_print_zpl2``: vai buscar o picking via
    ``context['active_id']`` e delega em
    ``stock_picking.action_print_zpl2(label_size)``.

- Templates ZPL (in-source em ``zpl_tags.py``):
  - Tamanho 55mm x 28mm (``^PW400``).
  - Logo Piccolo embebido como GFA monocromo no ``^FO0,10^GFA,...``.
  - Texto duplicado em duas linhas com offset de 1px (negrito
    "fake" - vejam ``^FO0,105`` e ``^FO1,106``).

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo. Garantir ``pycups`` no servidor e impressora
   ``ZEBRAP`` em CUPS.
2. Abrir um picking; clicar "Print ZPL Label" (botao adicionado por
   vista herdada).
3. No popup escolher o tamanho/template e confirmar.
4. A etiqueta e enviada para a Zebra.

e) Exemplo pratico
------------------
Picking ``WH/OUT/00120`` com 1 move de 5 unidades de "Cadeira X" e
``x_studio_volumes_3 = 2`` (vai em 2 volumes). Wizard com
``produtos``:
- Gera o ZPL com dados do picking (cliente, SO, ref).
- Imprime 2 etiquetas (uma por volume).

f) FAQ / Resolucao de problemas
-------------------------------
- *"Printer 'ZEBRAP' not found on the network"* -> a fila CUPS nao
  esta registada com esse nome. Editar a constante ``PRINTER_NAME``
  no ``_send_to_printer2`` ou renomear a fila CUPS.
- *"ImportError: No module named cups"* -> falta ``pycups`` no
  ambiente Python do servidor (``pip install pycups``).
- *"Etiqueta sai com caracteres estranhos"* -> ``^CI28`` (UTF-8)
  deveria ser suficiente; validar que o Zebra firmware suporta
  CI28.

g) Pontos de atencao / avisos
-----------------------------
- **HARDCODED**:
  - ``PRINTER_NAME = "ZEBRAP"``.
  - ``temp_file_path = "/tmp/zpl_print_job2.zpl"``.
  - Largura ``^PW400`` (55mm a 8 dpmm).
- **typos Studio mantidos literais** nos campos:
  ``x_studio_referncia_do_cliente`` (sem ``e``),
  ``x_studio_referncia_do_cliente_2``, ``x_studio_referncia_2``.
- **Substitui pg_zpl_tags v1.0** (sem wizard). Migrar instalacoes
  para esta versao.
- f-strings dentro do ZPL: cuidado com caracteres especiais nos
  campos de cliente/referencia (aspas, ^, ~) - podem partir o ZPL.
- Cada template imprime ``volume`` vezes; usar
  ``x_studio_volumes_3`` corretamente preenchido (via
  ``pg_cubicagem_wizard``).
""",
    'author': 'PG',
    'website': 'https://www.parametro.pt',

    'depends': ['sale_stock'],

    'assets': {
        'point_of_sale._assets': [
            'pg_zpl_tags/static/src/description/*',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/zpl_label_wizard_view.xml',
        'views/zpl_tags.xml',
    ],
    'installable': True,
    'application': False,
}
