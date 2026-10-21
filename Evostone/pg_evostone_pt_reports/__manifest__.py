# -*- coding: utf-8 -*-
{
    'name': 'EVOSTONE - Colunas de Pedra na Factura e na Guia (Portugal)',
    'version': '18.0.1.1.0',
    'category': 'Accounting/Accounting',
    'summary': 'Acrescenta S/N, dimensoes, unidade e peso as linhas da factura e da guia portuguesas',
    'description': '''
Poe na factura e na guia de transporte portuguesas as colunas de pedra que o
documento de Mocambique ja tinha.

Contexto
--------
A CFO enviou por email a FT/2026/00658 da STONE TRADING como modelo. Esse
documento sai pelo `mh_stone_reports`, que tem uma tabela de linhas com
`PRODUTO | S/N | QTD | COMP. | LAR. | ESP. | VOL./AREA/UNID. | UN | PRECO |
DESC. | SUBTOTAL`. A factura portuguesa sai pelo template standard do Odoo e
tem cinco colunas: `Descricao | Quantidade | Preco Unitario | Impostos |
Montante`. A guia portuguesa tem tres: `Produto | Encomendado | Entregue`.

Sem o numero de serie e as dimensoes, o cliente nao consegue reconciliar a
chapa que recebeu com a chapa que lhe foi facturada, que e' a razao de ser
destas colunas no negocio da pedra.

Desenho
-------
Heranca dos templates standard, nao reaproveitamento dos do `mh_stone_reports`.
Os templates de Mocambique sao autonomos e trazem o cabecalho Stone Trading;
adopta-los em Portugal faria perder o ATCUD, o codigo QR, a mencao
"Processado por programa certificado" e o circuito ORIGINAL/DUPLICADO do PT+,
que sao obrigatorios e ja funcionam. Herdando, as colunas entram e tudo o resto
fica intacto.

Nenhum campo novo: `lot_id`, `units_qty`, `length`, `width` e `thickness` ja
existem em `account.move.line` (mh_picking) e em `stock.move` /
`stock.move.line` (mh_inventory), e ja vem preenchidos em Portugal porque o
`mh_sale._prepare_invoice_line()` os propaga da linha de venda.

Decisoes
--------
1. A coluna `Impostos` mantem-se, embora o modelo de Mocambique nao a tenha: o
   artigo 36.o do CIVA exige a taxa aplicavel por linha.
2. A coluna `Desc.` continua condicional, ao contrario do modelo, que a mostra
   sempre. Com doze colunas a largura e' o constrangimento e uma coluna de
   zeros nao acrescenta informacao.
3. O corpo da tabela e' reduzido por uma classe CSS propria (`pg_stone_lines`),
   para caber em A4 retrato sem mexer no resto do layout.
4. As celulas de dimensao ficam em branco quando o valor e' zero, em vez de
   imprimirem `0.000`, para nao poluir as linhas de servico e de portes.

Os cabecalhos sao escritos em ingles e traduzidos em `i18n/pt.po`, para que um
cliente estrangeiro receba o documento coerente numa so lingua. Os msgid foram
extraidos da base com `base.language.export` e nao escritos a mao: uns termos
levam as etiquetas (`<span>Serial</span>`) e outros nao (`Units`), conforme o
`<th>` tenha ou nao um elemento la dentro, e um ficheiro com msgid errados
carrega sem dar erro e nao traduz nada. Ficheiro `pt.po` e nao `pt_PT.po`
porque o Odoo carrega primeiro a lingua base: um so ficheiro serve pt, pt_PT
e pt_BR.

As traducoes so entram na base quando o modulo e' **actualizado**; instalar o
codigo novo sem actualizar o modulo deixa os cabecalhos em ingles.

Porque nao ha bundle
--------------------
A primeira versao punha o CSS num `.scss` declarado em
`web.report_assets_common`. O ficheiro compila sem erro, verificado com dart-sass
e com libsass, que e' o compilador do Odoo, mas em staging a sua presenca no
bundle impedia a geracao do `web.report_assets_common` inteiro: TODOS os
relatorios da base sairam sem CSS nenhum - sem Lato, sem a faixa do layout
Folder, sem grelha - incluindo relatorios que este modulo nao toca. Desinstalar
o modulo devolvia o CSS.

Por isso o CSS vive agora num `<style>` dentro do proprio relatorio
(`stone_lines_style`), chamado pelos dois templates. E' o sitio certo para
estilo que so serve duas tabelas: nao entra no bundle global, nao o pode
partir, e nao obriga os outros relatorios a carrega-lo.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': [
        'account',
        'stock',
        'mh_picking',
        'mh_inventory',
        'ptplus',
        'ptplus_stock',
    ],
    'data': [
        'views/report_styles.xml',
        'views/report_invoice_document.xml',
        'views/report_delivery_document.xml',
        'views/report_layout_folder.xml',
    ],
    # Sem `assets`: ver a nota "Porque nao ha bundle" na descricao.
    'installable': True,
    'application': False,
    'auto_install': False,
}
