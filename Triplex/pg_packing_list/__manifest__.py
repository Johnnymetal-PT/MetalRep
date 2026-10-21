{
    'name': 'pg_packing_list',
    'version': '1.0',
    'summary': 'Dimensões, pesos e volume (CBM) nas transferências de stock, para o packing list',
    'description': """
pg_packing_list
===============

Objetivo de negócio
-------------------
Suportar o packing list / documento de expedição com a informação logística necessária:
dimensões, pesos (líquido e bruto), volume em CBM, nº de volumes e códigos HS.

Pré-requisitos
--------------
- Módulos: `base`, `product`, `stock`.
- Campo Studio `x_studio_dimenses` em `product.template` (criado via Studio).
- Produtos com `hs_code` preenchido para exportação (campo standard do Odoo).
- Dimensões e pesos preenchidos nas linhas das transferências (a entrada dos dados é manual).

Como funciona
-------------
Acrescenta campos e cálculos a três níveis e agrega-os para o relatório:
- `stock.move`: campos manuais depth/width/height, netWeight/grossWeight, `vol` (nº de
  volumes) e `volume_cbm` calculado (D x W x H x quantidade). Traz também, por campo
  related, as dimensões (`x_studio_dimenses`) e o `hs_code` do produto.
- `stock.move.line`: copia esses valores do respetivo move (compute) para ficarem
  disponíveis ao nível da linha.
- `stock.picking`: totais por transferência (somatórios) e concatenação de dimensões/HS.
- O relatório do packing list está em report/report_stockPicking_template.xml.

Passo a passo de utilização
---------------------------
1. Em cada movimento da transferência, preencher D/W/H (em metros, p.ex.), pesos e nº de volumes.
2. O `volume_cbm` é calculado automaticamente; os totais da entrega também.
3. Imprimir o packing list pela ação de relatório standard.
4. Validar que dimensões/HS aparecem agregados no cabeçalho do PDF.

Exemplo prático
---------------
Picking com 3 linhas: 0.6×0.8×1.0 m × 5 un = 2,4 CBM na primeira; somando com as outras, o
total de CBM aparece no relatório, e o HS Code de cada produto fica concatenado por vírgula.

FAQ / Resolução de problemas
----------------------------
- P: O volume em CBM saiu absurdo.
  R: D/W/H têm de estar todos na mesma unidade. Se forem em cm, o CBM = D×W×H×q/1.000.000;
     este módulo NÃO converte unidades — preencher diretamente em metros para ter CBM correto.
- P: O HS Code não aparece.
  R: Falta no produto (campo standard `hs_code`); preencher antes de imprimir.
- P: Tenho `pg_packing_list_triplex` também — qual usar?
  R: A variante Triplex é a mais completa (mais campos, wizard de cubicagem); validar qual
     está em uso no projeto.

Pontos de atenção
-----------------
- Depende do campo Studio `x_studio_dimenses` (product.template) e do `hs_code`.
- `volume_cbm` assume D/W/H na mesma unidade coerente com o CBM pretendido.
- Relacionado com `pg_packing_list_triplex` (variante específica) e `pg_packing_list_confirm`
  (bloqueio de validação).
""",
    'category': 'Inventory',
    'depends': ['base', 'product', 'stock'], 
    'data': [
        'views/qweb_report.xml',
        'report/report_stockPicking_template.xml',
    ],
    'installable': True, 
    'auto_install': False,               
    'application': False,               
}
