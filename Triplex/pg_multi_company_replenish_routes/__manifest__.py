{
    'name': 'PG Replenish Route Assignment',
    'version': '1.0',
    'summary': 'Cria automaticamente regras de reabastecimento (orderpoints) por armazém para produtos partilhados',
    'description': """
PG Replenish Route Assignment (Triplex / Oficinna)
==================================================

Objetivo de negócio
-------------------
Os produtos partilhados entre empresas (company_id=False) devem reabastecer de formas
diferentes em cada armazém:
- Armazém Triplex  -> rota "Buy" (comprar)
- Armazém Oficinna -> rota "Manufacture" (fabricar)

Para que o reabastecimento automático do Odoo funcione, cada variante precisa de uma regra
de reabastecimento (stock.warehouse.orderpoint) em cada armazém, com a rota correta. Este
módulo garante a existência dessas regras.

Pré-requisitos
--------------
- Módulos: `stock`, `product`.
- IDs reais do ambiente alinhados com os do código: armazéns 1 (Triplex) e 2 (Oficinna);
  rotas 5 (Buy) e 9 (Manufacture). Se forem diferentes, alterar o código antes de usar.
- Os produtos a tratar devem ser partilhados (sem empresa, company_id = False).

Como funciona
-------------
Estende `product.template`:
- `create()`: ao criar um novo produto partilhado, cria/reativa as orderpoints.
- `_create_reordering_rules_for_shared_products()`: por cada variante de cada template
  partilhado, reativa regras inativas existentes ou cria novas (min=0, max=10) no armazém
  Triplex (rota Comprar) e no armazém Oficinna (rota Fabricar).
- `add_routes_to_existing_templates()`: utilitário para correr manualmente (shell/ação de
  servidor) e aplicar as regras a TODOS os produtos já existentes.

Passo a passo de utilização
---------------------------
1. Confirmar os IDs de armazém/rota no código (TRIPLEX_WAREHOUSE_ID, BUY_ROUTE_ID, etc.).
2. Instalar/atualizar o módulo: os produtos novos passam a receber as regras automaticamente.
3. Para os produtos antigos, correr uma vez (em shell ou ação de servidor):
   `env['product.template'].search([]).assign_default_codes_to_all_variants` — não, neste
   módulo o método é `add_routes_to_existing_templates()`; correr esse sobre `product.template`.
4. Confirmar nas vistas de Inventário > Reabastecer que cada produto partilhado tem 2 regras.

Exemplo prático
---------------
Ao criar o produto "Cadeira X" partilhado -> são criadas duas orderpoints automaticamente:
uma no armazém Triplex com rota "Buy" (min 0, max 10) e outra no armazém Oficinna com
rota "Manufacture" (min 0, max 10).

FAQ / Resolução de problemas
----------------------------
- P: Criei um produto e não foram criadas regras.
  R: Confirmar que o produto é partilhado (sem empresa); produtos com empresa são ignorados.
- P: Quero outros mínimos/máximos.
  R: Os valores 0/10 estão fixos no código; alterar `_create_reordering_rules_for_shared_products`.
- P: Já existem regras inativas — vão duplicar?
  R: Não — regras inativas existentes são REATIVADAS em vez de criar novas.

Pontos de atenção
-----------------
- IDs FIXOS no código (armazéns 1/2, rotas 5/9); obrigatório rever em novo ambiente.
- Usa sudo() para contornar regras de acesso ao criar/ler em multi-empresa.
- `create` usa assinatura single-record (não `@api.model_create_multi`).
- Relacionado com `pg_multi_company_routes` (aborda rotas pela venda, atualmente inativo).
""",
    'author': 'PG',
    'depends': ['stock', 'product'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
