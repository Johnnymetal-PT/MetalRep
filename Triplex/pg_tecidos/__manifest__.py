{
    'name': 'PG Tecidos Customization',
    'version': '1.0',
    'summary': 'Gera automaticamente a lista de materiais (BOM) de cada Ordem de Fabrico com os tecidos/materiais escolhidos na variante',
    'description': """
PG Tecidos Customization
========================

Objetivo de negócio
-------------------
Os móveis/estofos da Triplex têm a mesma estrutura mas tecidos/peles/acabamentos diferentes
por encomenda. Em vez de manter uma lista de materiais (BOM) por combinação, este módulo
constrói automaticamente uma BOM dedicada para cada Ordem de Fabrico, com os materiais
corretos lidos da descrição/variante da venda.

Pré-requisitos
--------------
- Módulos: `mrp`, `stock`, `sale`.
- Existir uma BOM "modelo" para o produto (é duplicada e adaptada).
- Os componentes da BOM devem ter no nome os termos reconhecidos (Tecido, Tecido1..3, Pele,
  Pele1..3, Vivos, Acabamento, Metal, Estrutura, Costa Exterior, Costa Interior e Assento).
- Tabela de consumo no produto componente (campos price_1..price_10 — ver `pg_price_table`).
- Fornecedores (product.supplierinfo) configurados nos componentes (para o stock.move).

Como funciona
-------------
- `mrp.production.create()`: ao criar a OF (origem = venda),
  1. preenche `description_sale` a partir da linha de venda;
  2. extrai os termos (Tecido:, Pele:, etc.) da descrição e os "TX" do nome do produto
     (categorias de tecido entre parênteses);
  3. encontra a BOM mais antiga do produto, duplica-a e escala as quantidades;
  4. aplica as quantidades de consumo (tabela price_1..10) por escalão;
  5. para cada termo, duplica o componente e renomeia-o com o tecido/material escolhido;
  6. associa a BOM duplicada à OF.
- `stock.rule._run_manufacture()`: cria as OFs em estado "rascunho" a partir do
  reabastecimento, garantindo que passam pela lógica acima.
- `stock.move`: calcula o `partner_id` (fornecedor) do componente a partir do
  product.supplierinfo e, ao mudar o fornecedor na linha, atualiza/cria o supplierinfo.
- `sale.order`: alertas de compromisso (`is_commitment_overdue`/`is_commitment_soon`,
  janela de 3 semanas) e etiquetas personalizadas (`sale.order.tag`).

Passo a passo de utilização
---------------------------
1. Garantir a BOM modelo, os termos nos nomes dos componentes e a tabela de consumo.
2. Confirmar a venda com a descrição/variante a indicar os tecidos.
3. Ao gerar a Ordem de Fabrico, a BOM dedicada é criada automaticamente com os materiais certos.
4. Validar a OF/BOM gerada antes de produzir.

Exemplo prático
---------------
Venda de um sofá com "Tecido: Veludo Verde; Vivos: Bege". A OF criada terá uma BOM própria
em que o componente genérico "Tecido" foi substituído por um produto "Veludo Verde" e o
"Vivos" por "Bege", com as quantidades de consumo do escalão correspondente à quantidade.

FAQ / Resolução de problemas
----------------------------
- P: A OF foi criada sem BOM dedicada.
  R: Confirmar que existe uma BOM modelo para o produto e que os componentes têm os termos
     reconhecidos no nome.
- P: As quantidades de tecido estão erradas.
  R: Rever a tabela de consumo (price_1..10) do componente e a quantidade da OF.
- P: Foram criados muitos produtos duplicados.
  R: É esperado: cada material escolhido gera/reutiliza um produto com o nome correspondente.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Existem DOIS métodos `create` em mrp_production.py; em Python o segundo anula o primeiro,
  pelo que o primeiro (linhas ~20-30) é código morto. Rever/remover.
- A correspondência de termos e fornecedores assenta em texto nos nomes dos produtos — frágil
  a mudanças de nomenclatura.
- Cria/duplica produtos e BOMs em massa; testar em ambiente de teste antes de produção.
- Partilha a "tabela de consumo" (price_1..10) com `pg_price_table`.
""",
    'depends': ['mrp', 'stock', 'sale'],
    'data': [
        'views/pg_tecidos_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}

