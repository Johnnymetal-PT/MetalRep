{
    'name': 'Multi-Company Routes: Oficinna 22',
    'version': '1.0',
    'summary': 'Força rotas de abastecimento (Comprar/Fabricar + MTO) por empresa ao confirmar a venda',
    'description': """
Multi-Company Routes (Triplex / Oficinna22)
===========================================

Objetivo de negócio
-------------------
Em ambiente multi-empresa, os produtos partilhados (sem empresa, company_id=False)
têm de seguir rotas de abastecimento diferentes consoante a empresa que vende:
- Triplex (company_id = 1): rotas "Buy" + "Replenish on Order (MTO)"
- Oficinna22 (company_id = 2): rotas "Manufacture" + "Replenish on Order (MTO)"

Pré-requisitos
--------------
- Módulos: `stock`, `mrp`, `sale`.
- Existirem as rotas "Buy", "Manufacture" e "Replenish on Order (MTO)" por empresa.
- Os IDs reais das empresas têm de corresponder aos do código (1 = Triplex, 2 = Oficinna22).
- ATENÇÃO: o módulo só funciona depois de ativado (ver Pontos de atenção).

Como funciona
-------------
Estende `sale.order` (ver models/product_template.py) e, no `action_confirm()`,
ANTES de confirmar a venda:
1. Determina as rotas obrigatórias a partir da empresa da encomenda.
2. Procura essas `stock.route` para essa empresa.
3. Para cada produto partilhado das linhas, substitui `route_ids` pelas rotas
   corretas (só escreve se forem diferentes das atuais).

Passo a passo de utilização
---------------------------
1. Ativar o módulo (descomentar a importação dos modelos no __init__.py — ver Pontos de atenção).
2. Confirmar uma encomenda de venda na empresa pretendida.
3. As rotas dos produtos partilhados ficam ajustadas automaticamente à empresa.

Exemplo prático
---------------
Encomenda na Triplex com um sofá partilhado -> ao confirmar, o sofá fica com as rotas
"Buy" + "MTO". A mesma referência vendida pela Oficinna22 fica com "Manufacture" + "MTO".

FAQ / Resolução de problemas
----------------------------
- P: Confirmei a venda e as rotas não mudaram.
  R: O módulo está inativo (__init__.py vazio) ou os IDs de empresa não correspondem.
- P: Tenho mais empresas além de 1 e 2.
  R: As empresas não previstas são ignoradas; é preciso alterar o código para as suportar.
- P: Não quero mexer nos produtos com empresa.
  R: É o comportamento atual — só os produtos partilhados (sem empresa) são ajustados.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Os IDs de empresa (1, 2) e os nomes de rotas estão fixos no código; rever em novo ambiente.
- Só atua sobre produtos partilhados (company_id=False).
- O `__init__.py` na raiz está vazio, logo os modelos NÃO são carregados e este override NÃO
  está ativo na prática. A view `views/product_template_views.xml` também está comentada no
  manifesto. Comparar com `pg_multi_company_replenish_routes` (resolve problema semelhante
  por reordering rules).
""",
    'category': 'Inventory',
    'author': 'Your Name',
    'depends': ['stock', 'mrp', 'sale'],
    'data': [
        #'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
