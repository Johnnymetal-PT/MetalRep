# -*- coding: utf-8 -*-

{
    'name': 'PG Pesquisa por Referencia Interna',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Permite pesquisar variantes pela referencia interna usada pela Essani.',
    'description': '''
Objetivo de negocio
===================
Facilita a pesquisa de artigos quando a equipa conhece a referencia interna da Essani/PHC, mas nao o nome comercial do produto.

Pre-requisitos
==============
Modulo Product instalado. Campo Studio/custom `x_studio_referncia_interna` existente em `product.product`; se o campo for renomeado, o modulo deixa de pesquisar por referencia interna.

Como funciona
=============
Herda `product.product` e altera `name_search` para procurar por nome, `default_code` e `x_studio_referncia_interna`. Tambem altera `name_get` para mostrar a referencia entre parenteses retos antes do nome.

Passo a passo de utilizacao
===========================
1. Instalar ou atualizar o modulo. 2. Preencher `Referencia Interna` nas variantes. 3. Usar qualquer campo many2one de produto em vendas/compras/stock e pesquisar pela referencia.

Exemplo pratico
===============
Ao pesquisar `ABC123` numa linha de venda, o Odoo encontra a variante cujo `x_studio_referncia_interna` e `ABC123` e apresenta `[ABC123] Nome do Produto`.

FAQ / Resolucao de problemas
============================
Se nao encontra resultados, confirmar se a referencia esta na variante e nao apenas no template. Se aparecer uma referencia vazia, validar `default_code` e `x_studio_referncia_interna`. Se der erro de campo inexistente, recriar ou ajustar o campo Studio.

Pontos de atencao / avisos
==========================
Override transversal de `name_search`/`name_get`: afeta todos os locais onde se escolhem variantes. O campo tem o nome historico `x_studio_referncia_interna` sem acento/correcao ortografica; nao alterar sem migracao.
''',
    'depends': ['base', 'product', 'sale'],
    'data': [],
    'installable': True,
    'application': False,
}
