{
    'name': 'PG Variant Upload with Custom Attributes',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Importa produtos, atributos, variantes e suplementos de preço a partir de um Excel',
    'description': """
PG Variant Upload with Custom Attributes
========================================

Objetivo de negócio
-------------------
Criar/atualizar em massa o catálogo a partir de um Excel: produtos, atributos, valores de
variante e respetivos suplementos de preço (price_extra), evitando a introdução manual de
centenas de combinações.

Pré-requisitos
--------------
- Módulos: `product`.
- Biblioteca Python `pandas` instalada no servidor.
- Ficheiro Excel no formato esperado (ver abaixo).

Formato do Excel
----------------
- Linha 1 (índice 0): categorias de atributo (células fundidas; o módulo preenche para a direita).
- Linha 2 (índice 1): cabeçalho das variantes (colunas "Atributos" e "Variantes" são ignoradas).
- Linha 3 em diante: um produto por linha (coluna 0 = nome do produto); cada célula é o valor
  do atributo dessa coluna. Valores NUMÉRICOS são tratados como price_extra do valor; valores
  de TEXTO são guardados como "atributo personalizado" (custom.product.attribute) do produto.

Como funciona
-------------
- `product.import.wizard`: recebe o ficheiro e chama o importador.
- `product.import.import_file()`: lê o Excel com pandas, cria os atributos/valores em falta,
  associa-os aos produtos (criando o produto se não existir), grava o price_extra e regista
  os atributos de texto como `custom.product.attribute`.
- `custom.product.attribute(.value)`: modelos para os atributos descritivos (texto).
- `product.template.custom_attribute_ids`: lista desses atributos personalizados no produto.

Passo a passo de utilização
---------------------------
1. Preparar o Excel no formato acima.
2. Abrir o assistente de importação, carregar o ficheiro e executar.
3. Validar os produtos/atributos/variantes criados e os price_extra aplicados.

Exemplo prático
---------------
Linha do produto "Cadeira X": coluna "COR -> Azul" com valor 15 -> cria a variante Azul e
define price_extra=15; coluna "NOTA -> tecido especial" (texto) -> guarda como atributo
personalizado descritivo do produto.

FAQ / Resolução de problemas
----------------------------
- P: A importação rebenta com erro do pandas.
  R: O tratamento de exceções no import está comentado (ver Pontos de atenção); os erros
     propagam-se em bruto. Verificar o formato do Excel e o `pandas` instalado.
- P: Criou produtos a mais/errados.
  R: A correspondência de produto é por nome (ilike); nomes ambíguos podem criar/associar mal.
- P: As colunas "Atributos"/"Variantes" foram ignoradas.
  R: É intencional — são colunas de cabeçalho do template.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Existe bastante CÓDIGO MORTO: o ficheiro `wizards/product_import_wizard.py` está totalmente
  comentado e há um grande bloco comentado no fim de `models/product_import_wizard.py`.
- O `try/except` que protegia a importação está comentado — uma falha a meio deixa dados
  parcialmente importados. Idealmente correr em ambiente de teste primeiro.
- A view do assistente está comentada no manifesto (`views/product_import_wizard_view.xml`).
- Importação pesada deve ser feita fora de horas de pico.
""",
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        #'views/product_import_wizard_view.xml',
    ],
    'installable': True,
    'application': False,
}
