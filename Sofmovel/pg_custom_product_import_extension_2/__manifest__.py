{
    'name': 'PG Custom Product Import Extension Sofmovel',
    'version': '1.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Importacao em massa de produtos com tag Sofmovel a partir de Excel (cria, atualiza, arquiva e gere variantes Cor).',
    'description': """
PG Custom Product Import Extension Sofmovel
===========================================

a) Objetivo de negocio
----------------------
Sincronizar o catalogo proprio "Sofmovel" no Odoo a partir de um ficheiro Excel.
Semelhante ao [[pg_custom_product_import_extension]] (Kave), mas dedicado a
produtos com tag "Sofmovel" e com o seguinte:
- Match por `x_studio_referncia_interna` (campo Studio) ou
  `x_studio_cdigo_de_barras` (campo Studio).
- Suporta multiplos valores de "Colour" (vai criar atributos custom "Cor").
- Arquiva produtos Sofmovel ativos que deixem de constar no ficheiro.

[PONTO POR VALIDAR] Este modulo nao tem o nivel de robustez do Kave (sem
retries, sem savepoints por linha, sem email de resumo). Confirmar se ainda
esta em uso ou se foi substituido pelo padrao Kave/PIM.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `sale`, `web`.
- Bibliotecas Python: `pandas`, `openpyxl`.
- Tag "Sofmovel" em `product.tag` (criada se nao existir).
- Categorias "Produtos Sofmovel" em `product.category`, `product.public.category`
  e `pos.category` (criadas automaticamente sob "All"/"Todas").
- Campos Studio: `x_studio_referncia_interna`, `x_studio_cdigo_de_barras`,
  `x_studio_quantidade_em_stock`, `x_studio_stock_em_7_dias`,
  `x_studio_stock_em_15_dias`, `x_studio_stock_em_30_dias`,
  `x_studio_preo_antes_desconto`, `x_studio_desconto_aplicado_1`,
  `x_studio_data_estimada_de_entrega`.
- Modelo custom `custom.product.attribute` (do [[pg_variant_upload]]) para
  guardar os valores de Cor por produto.

c) Como funciona
----------------
- `models/product_import_sofmovel_wizard.py` define
  `product.import.sofmovel.wizard` (TransientModel) com `action_import`:
  1. Le XLSX com pandas, normaliza colunas obrigatorias e numericos
     em formato PT.
  2. Cria tag/categorias Sofmovel se nao existirem.
  3. Calcula a lista de codigos importados; arquiva (active=False) todos os
     templates Sofmovel cujo `x_studio_referncia_interna` / `default_code` /
     variantes nao constem do XLSX.
  4. Para cada linha:
     a. Pesquisa por `x_studio_referncia_interna` com tag Sofmovel; senao por
        `x_studio_cdigo_de_barras`.
     b. Le "Colour" (CSV) e cria registos `custom.product.attribute` com
        name="Cor" e description=valor.
     c. CREATE se nao existir; senao UPDATE com os mesmos campos.
     d. Atualiza acessorios por agrupamento de `Program` (mesma logica que
        Kave).
     e. (Bloco de supplierinfo comentado - PONTO POR VALIDAR se e para
        reactivar.)
     f. Cria/atualiza `stock.quant` em `stock.stock_location_stock`.
     g. Calcula `sale_delay` a partir de Estimated Date ou de stock
        progressivo.
  5. Sem email de resumo no final.
- `views/product_import_menu.xml` adiciona o menu "Importar Produtos Sofmovel".

d) Passo a passo de utilizacao
------------------------------
1. Validar tag/categorias e campos Studio.
2. Menu Inventario / Importacoes / Importar Produtos Sofmovel.
3. Carregar XLSX (colunas: Code, EAN Code, Program, Description, Stock,
   Purchase Price, Discount, Nett Purchase Price, Recommended Retail Price,
   Suggested Retail Price, Colour, Weight Package, Stock Blue, Stock Red,
   Stock Grey, Estimated Date (dd/mm/yyyy)).
4. Executar. Acompanhar progresso no log.

e) Exemplo pratico
------------------
- Linha XLSX:
  - Code = "SOF-001", EAN = 5601111122222, Program = "Sofa Aveiro",
    Colour = "Cinza, Castanho, Bege".
- Resultado:
  - Cria template SOF-001 com tag Sofmovel, categorias Sofmovel, publicado.
  - Cria 3 `custom.product.attribute` para o template:
    Cor=Cinza, Cor=Castanho, Cor=Bege.
  - Cria quant em `stock.stock_location_stock`.

f) FAQ / Resolucao de problemas
-------------------------------
- "UserError: Coluna obrigatoria em falta":
  Verificar todas as colunas listadas em c).
- "Produto nao foi encontrado":
  O wizard procura por `x_studio_referncia_interna` (Studio) + tag Sofmovel.
  Se a referencia for diferente da do Excel, nao faz match. Verificar tambem
  `x_studio_cdigo_de_barras`.
- "Custom attribute Cor duplicado":
  O wizard verifica se ja existe um `custom.product.attribute` com a mesma
  combinacao (product_id + name + description) antes de criar. Se duplicar,
  validar se os valores no XLSX vem com espacos extra.

g) Pontos de atencao
--------------------
- Sem retries nem savepoints por linha; uma falha SQL pode comprometer a
  transacao toda. Recomenda-se correr em horarios calmos.
- Bloco de supplierinfo desativado por comentario; se for necessario, ver
  TODO no codigo.
- Codigo usa `default_code` E `x_studio_referncia_interna` em simultaneo; o
  match e cruzado.

[FACTO OBSERVADO] versao mais simples que o equivalente Kave.
    """,
    'depends': ['base', 'product', 'sale', 'web'],
    'data': [
        'views/product_import_menu.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
