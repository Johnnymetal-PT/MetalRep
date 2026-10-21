{
    'name': 'PG Dynamic Consumption Table for Manufacturing Orders',
    'version': '1.0',
    'summary': 'Define a quantidade a consumir nas Ordens de Fabrico a partir de uma tabela por escalão de quantidade no produto',
    'sequence': 1,
    'description': """
PG Dynamic Consumption Table (Tabela de Consumo nas Ordens de Fabrico)
======================================================================

Objetivo de negócio
-------------------
A quantidade de matéria-prima a consumir (campo "Para Consumir") não é linear: depende do
escalão de quantidade a produzir. Cada produto tem uma "Tabela de Consumo" com 10 valores
(escalões 1 a 10); a Ordem de Fabrico (MO) deve usar o valor do escalão certo, em particular
para o componente "Tecido de Fornecedor".

Pré-requisitos
--------------
- Módulos: `mrp`, `stock`.
- Cada produto que entre em MOs deve ter a Tabela de Consumo (price_1..price_10) preenchida.
- A BOM do produto deve incluir um componente cujo nome é exatamente "Tecido de Fornecedor"
  (o módulo procura por nome).
- Compatível com `pg_tecidos` (que partilha a mesma tabela price_1..price_10).

Como funciona
-------------
- `product.template`: acrescenta 10 campos `price_1`..`price_10`. ATENÇÃO ao nome — apesar
  de se chamarem "price", guardam QUANTIDADES de consumo por escalão, não preços.
- `mrp.production.create()`: ao criar a MO, lê a tabela do produto via
  `_get_consumption_value(template, product_qty)` e:
    * define `product_uom_qty` da MO com o valor do escalão correspondente;
    * percorre os movimentos de componentes (`move_raw_ids`) e, no movimento cujo produto
      é "Tecido de Fornecedor", força a quantidade planeada para o mesmo valor.
- `_get_consumption_value()`: escolhe o valor por escalão — qty<=1 -> price_1,
  qty<=2 -> price_2, ... qty<=10 -> price_10; acima de 10 usa o último valor.

Passo a passo de utilização
---------------------------
1. No produto a fabricar, preencher os campos `price_1`..`price_10` (quantidades a consumir).
2. Confirmar que a BOM tem o componente "Tecido de Fornecedor".
3. Criar a MO (manual ou via reabastecimento). O `product_uom_qty` e o movimento do tecido
   ficam ajustados ao escalão automaticamente.
4. Validar visualmente a quantidade a consumir antes de iniciar a produção.

Exemplo prático
---------------
Produto "Sofá Y" com tabela: price_1=2.0, price_2=3.5, price_3=4.8, ..., price_10=14.
- MO para 1 sofá -> Para Consumir = 2.0 m de Tecido de Fornecedor.
- MO para 3 sofás -> Para Consumir = 4.8 m de Tecido de Fornecedor (não 6.0).
- MO para 12 sofás -> usa o valor de price_10 (último escalão).

FAQ / Resolução de problemas
----------------------------
- P: O "Para Consumir" não é alterado.
  R: Confirmar que o produto tem `price_1..price_10` preenchidos e que existe um componente
     na BOM chamado exatamente "Tecido de Fornecedor".
- P: Tenho um produto que não usa "Tecido de Fornecedor"; o que acontece?
  R: A MO recebe `product_uom_qty` do escalão, mas não há override de nenhum componente.
- P: Quero mais de 10 escalões.
  R: Não é possível sem alterar o módulo (a tabela está fixa em 10 valores).
- P: Como evito conflito com `pg_tecidos`?
  R: Ambos usam os mesmos campos `price_N`; coexistem mas é importante saber qual módulo
     está a determinar o consumo da MO em cada cenário.

Pontos de atenção
-----------------
- O nome do componente "Tecido de Fornecedor" está fixo no código (match por nome).
- Tabela limitada a 10 escalões.
- `create` usa assinatura single-record (não `@api.model_create_multi`).
""",
    'category': 'Manufacturing',
    'author': 'Your Name',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/product_template_views.xml',  # Add the consumption table field to the product backoffice
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

