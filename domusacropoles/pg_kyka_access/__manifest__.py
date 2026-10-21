# -*- coding: utf-8 -*-
# Parâmetro Global - Cliente Domus & Acrópoles (Kyka)
{
    "name": "PG Kyka - Matriz de Acessos",
    "author": "Parâmetro Global",
    "website": "https://parametro.global",
    "version": "18.0.1.2.0",
    "license": "LGPL-3",
    "category": "Tools",
    "summary": "Matriz de permissões dos utilizadores Kyka: grupos de consulta, "
               "read-only em Vendas/Projeto, contabilidade vendor-only e menus.",
    "description": """
Aplica a matriz de acessos pedida pelo cliente (Domus & Acrópoles):

- Grupos de consulta (read-only) para Projeto, Compras, Vendas e Inventário,
  espelhando o âmbito de leitura do grupo funcional de cada app.
- Override dos ACLs standard que dão escrita a sale.order (Faturação/Contabilidade/
  Inventário) e project.task (Utilizador Interno), para permitir perfis de consulta.
- Perfil de contabilidade "só fornecedores" para o Francisco (leitura via grupo aux,
  escrita limitada a faturas de fornecedor via grupo de Compras), com menu Clientes
  escondido e cartão de cliente do Painel oculto.
- Atribuição dos 4 utilizadores segundo a matriz.
- Ana Sousa promovida a Inventário / Administrador (stock_mgr) para aceder às
  Categorias de Produtos via Inventário -> Configuração.

A lógica é idempotente e reaplicada em cada install/update do módulo, por isso
sobrevive aos upgrades do Odoo.sh que reponham os ACLs/menus standard.
""",
    "depends": [
        "base",
        "sale_management",
        "purchase",
        "stock",
        "project",
        "account",
        "project_purchase",
    ],
    "data": [
        "data/apply.xml",
    ],
    "installable": True,
    "application": False,
}
