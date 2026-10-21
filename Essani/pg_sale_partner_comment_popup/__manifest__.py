# -*- coding: utf-8 -*-

{
    'name': 'PG Aviso Comentario Cliente em Vendas',
    'version': '19.0.1.0.0',
    'category': 'Sales',
    'summary': 'Mostra o comentario do contacto ao escolher cliente em orcamentos.',
    'description': '''
Objetivo de negocio
===================
Garante que notas importantes do contacto são vistas pelo comercial antes de avançar com o orçamento.

Pre-requisitos
==============
Modulo Sales instalado. Campo standard `res.partner.comment` preenchido nos contactos relevantes.

Como funciona
=============
Herda `sale.order` e usa `@api.onchange('partner_id')` para devolver warning com o comentário convertido de HTML para texto simples.

Passo a passo de utilizacao
===========================
1. Preencher notas internas/comentário no contacto. 2. Criar orçamento. 3. Selecionar cliente. 4. Ler o popup de aviso.

Exemplo pratico
===============
Cliente `Empresa X` tem comentário `Enviar sempre proposta com portes`. Ao selecioná-lo no orçamento, aparece aviso com essa nota.

FAQ / Resolucao de problemas
============================
Se não aparece, confirmar se o comentário está no contacto selecionado e não apenas na empresa-mãe. Se o texto vem com HTML, validar origem do campo `comment`.

Pontos de atencao / avisos
==========================
Só atua no onchange da interface. Importações/API que definem `partner_id` não mostram popup.
''',
    'author': 'PG',
    'license': 'LGPL-3',
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'application': False,
}
