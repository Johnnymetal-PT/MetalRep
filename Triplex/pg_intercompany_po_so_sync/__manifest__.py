{
    "name": "PG Intercompany PO SO Sync",
    "version": "17.0.1.0.0",
    "summary": "Preserva descrição e anexos das linhas da PO ao gerar a venda intercompany",
    "description": """
PG Intercompany PO SO Sync
==========================

Objetivo de negócio
-------------------
Quando uma empresa do grupo emite uma compra (purchase.order) a outra empresa do grupo, o
Odoo cria automaticamente a venda correspondente (sale.order) na empresa fornecedora (regras
"Inter Company"). No standard, esse processo perde informação das linhas: a descrição
personalizada e os anexos por linha não passam para a SO. Este módulo preserva essa
informação.

Pré-requisitos
--------------
- Módulos: `sale_purchase_inter_company_rules`, `pg_product_multi_attachment`.
- Multi-empresa configurado com utilizador intercompany e regras Inter Company ativas.
- As linhas de compra/venda têm de suportar o campo `attachment_ids` (vem de pg_product_multi_attachment).
- Listas de preços com moeda coerente entre compra e venda intercompany.

Como funciona
-------------
Estende `purchase.order` e reescreve o fluxo intercompany:
- `inter_company_create_sale_order()`: recria a SO a partir da PO e, no fim, reaplica o
  `name` (descrição) de cada linha da PO na linha correspondente da SO (emparelhamento por
  sequência/id). Mantém as validações standard (utilizador intercompany, direitos de acesso,
  coerência de moeda) e, se a empresa estiver configurada para tal, confirma a SO automaticamente.
- `_prepare_sale_order_line_data()`: acrescenta `attachment_ids` aos valores da linha de
  venda, copiando os anexos da linha de compra.
- Helpers `_can_create_sale_order` e `_should_auto_confirm_intercompany_document` usam
  introspeção (hasattr / verificação de campo) para funcionar em diferentes versões.

Passo a passo de utilização
---------------------------
1. Garantir que o utilizador intercompany está configurado e tem permissões em ambas as empresas.
2. Numa empresa, criar e confirmar uma encomenda de compra a uma empresa do grupo.
3. A SO é criada automaticamente na outra empresa, já com descrição original e anexos das linhas.
4. Se a empresa de destino tiver `intercompany_document_state = "posted"`, a SO é confirmada também.

Exemplo prático
---------------
A "Triplex" compra à "Oficinna" 5 cadeiras, com descrição "Tecido especial cliente X" e a
ficha técnica em anexo. Ao confirmar a PO, a SO criada na Oficinna mantém a mesma descrição
em cada linha e leva a ficha técnica anexada.

FAQ / Resolução de problemas
----------------------------
- P: A SO foi criada mas a descrição é a standard do produto.
  R: Confirmar que este módulo está instalado e ativo no fluxo (o módulo standard, sozinho,
     perde a descrição personalizada).
- P: Os anexos não passaram.
  R: Verificar que `pg_product_multi_attachment` está instalado e que as linhas da PO têm anexos.
- P: Erro "Provide at least one user for inter company relation".
  R: Falta o `intercompany_user_id` nas Definições da empresa de destino.
- P: Erro de moeda diferente entre PO e lista de preços.
  R: Alinhar a moeda da PO com a moeda da lista de preços do parceiro-empresa.

Pontos de atenção
-----------------
- O emparelhamento de linhas é feito por (sequence, id); manter as linhas estáveis até à criação da SO.
- Override de um fluxo central do intercompany; atualizações major do Odoo exigem revisão.
- Relacionado com `pg_description` (que respeita o contexto `intercompany_preserve_line_name`).
""",
    "author": "PG",
    "category": "Sales/Purchase",
    "depends": [
        "sale_purchase_inter_company_rules",
        "pg_product_multi_attachment",
    ],
    "data": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "AGPL-3",
}
