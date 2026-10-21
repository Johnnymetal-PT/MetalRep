# -*- coding: utf-8 -*-

{
    'name': 'PG Importacao Produtos Kave',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Importa ficheiro Excel Kave e atualiza produtos, stock, categorias e fornecedores.',
    'description': '''
Objetivo de negocio
===================
Automatiza a atualização de artigos Kave Home a partir do ficheiro Excel do fornecedor, reduzindo trabalho manual e mantendo produtos obsoletos arquivados.

Pre-requisitos
==============
Bibliotecas Python `pandas` e motor Excel disponíveis no ambiente. Fornecedor `Kave Home` criado. Rotas e localizações esperadas existem. Campos Studio de stock/preço usados pelo cliente existem. IDs fixos: template email 80, imposto IVA 1567, localização 54 e empresa 2.

Como funciona
=============
Wizard lê Excel, valida colunas, normaliza preços/EAN, cria tag/categorias `Kave`, arquiva produtos ausentes, cria/reativa/atualiza produtos, fornecedores, stock quants, datas estimadas e regras de reabastecimento.

Passo a passo de utilizacao
===========================
1. Abrir produto ou menu de importação. 2. Carregar Excel Kave. 3. Clicar `Importar`. 4. Rever logs e produtos criados/arquivados. 5. Confirmar stock e preço no website.

Exemplo pratico
===============
Linha Excel com Code `KH001`, Program `Mesa X`, Stock 3 e Recommended Retail Price 100 cria/atualiza o produto `Mesa X`, marca com tag Kave, publica no website e atualiza stock em KAV/Stock.

FAQ / Resolucao de problemas
============================
Erro de coluna em falta: usar o template Excel esperado. Erro `Vendor Kave Home not found`: criar fornecedor. Taxa não atribuída: validar ID 1567. Stock no local errado: validar localização 54 e empresa 2 antes de executar em produção.

Pontos de atencao / avisos
==========================
Modulo operacional mas muito específico. Contém IDs hardcoded e commits dentro do loop; antes de reutilizar noutro cliente, parametrizar IDs e testar em staging. Campo `x_studio_referncia_interna` é dependência funcional.
''',
    'author': 'Parametro Global SA',
    'depends': ['base', 'product', 'sale', 'web'],
    'data': ['views/product_import_menu.xml', 'security/ir.model.access.csv'],
    'installable': True,
    'application': False,
}
