{
    "name": "PG Description Enhancements",
    "version": "1.1",
    "summary": "Limpa e formata automaticamente a descrição das linhas de venda a partir dos atributos da variante",
    "author": "Your Name",
    "website": "https://yourwebsite.com",
    "category": "Sales",
    "depends": [
        "sale",  # módulo base de vendas
        "website_sale",  # necessário porque também afeta o carrinho/loja
    ],
    "description": """
PG Description Enhancements
===========================

Objetivo de negócio
-------------------
As descrições das linhas de venda, geradas a partir das variantes, vêm "poluídas" com
termos internos (categorias de preço, "Cliente", "Mesmo Tecido", etc.) e mal organizadas.
Este módulo limpa e reorganiza essa descrição para ficar apresentável ao cliente, tanto na
encomenda como no carrinho/checkout do website.

Pré-requisitos
--------------
- Módulos: `sale`, `website_sale`.
- Atributos/variantes configurados (a descrição base vem dos atributos da variante).

Como funciona
-------------
- `sale.order.line`:
    * `_process_name_field()`: lógica central de limpeza — extrai termos entre parênteses,
      remove termos excluídos (categorias, "Cliente", etc.), trata casos especiais de TECIDO
      e reorganiza o texto final.
    * É aplicada em `create`, `write` e `onchange` do campo `name`.
    * `cart_processed_description` (Html, calculado): versão da descrição para o carrinho,
      com quebras de linha antes de termos-chave (ACABAMENTO:, PINTURA:, TECIDO 1:, ...).
- `sale.order.write()`: quando a encomenda passa a "Enviada"/"Confirmada", reprocessa as
  descrições de todas as linhas.
- Respeita o contexto `intercompany_preserve_line_name` (não reprocessa quando a venda é
  gerada por fluxo intercompany — ver `pg_intercompany_po_so_sync`).

Passo a passo de utilização
---------------------------
1. Instalar; não requer configuração nem alteração de vistas.
2. Criar/editar linhas de venda normalmente — a descrição é limpa automaticamente.
3. No website, o carrinho/checkout mostra a descrição já processada.

Exemplo prático
---------------
Descrição original "Cadeira X (Categoria B, Cliente) TECIDO CIMA: Azul" passa a algo como
"Cadeira X\\nTECIDO: Azul" (remove a categoria/cliente e simplifica TECIDO CIMA -> TECIDO).

FAQ / Resolução de problemas
----------------------------
- P: A descrição não está a ser limpa.
  R: Verificar se a linha está a ser criada por fluxo intercompany (esse é propositadamente ignorado).
- P: Falta uma quebra de linha antes de um termo.
  R: A lista de termos com quebra está fixa no código (_compute_cart_processed_description).
- P: Removeu algo que eu queria manter.
  R: Os "termos excluídos" estão fixos em `_process_name_field`; ajustar no código se necessário.

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- Acrescenta um estado extra 'automation_trigger' à `sale.order` (usado por automações).
- A limpeza assenta em listas de termos/padrões fixos no código (específicos da Triplex);
  novos termos exigem alteração ao módulo.
- `create` usa assinatura single-record (não `@api.model_create_multi`).
""",
    "data": [
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}

