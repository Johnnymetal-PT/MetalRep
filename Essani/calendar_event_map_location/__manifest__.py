# -*- coding: utf-8 -*-

{
    'name': 'PG Calendario no Mapa por Localizacao',
    'version': '19.0.1.0.0',
    'category': 'Hidden',
    'summary': 'Permite geocodificar eventos de calendario pelo campo Localizacao.',
    'description': '''
Objetivo de negocio
===================
Permite usar a vista de mapa em reuniões mesmo quando o local relevante está escrito em `Localização`, e não na morada do contacto.

Pre-requisitos
==============
Modulos Calendar e Web Map instalados. Serviço de geocoding configurado/permitido pelo Odoo conforme a vista de mapa standard.

Como funciona
=============
Herda `calendar.event` para guardar um contacto principal e preencher por defeito a partir do utilizador. Patch JS do `MapModel` inclui o campo `location` e cria um pseudo-partner em memória para geocoding; evita escrever coordenadas em pseudo IDs.

Passo a passo de utilizacao
===========================
1. Criar reunião com campo `Localização` preenchido. 2. Abrir vista de mapa do calendário. 3. Confirmar marcador pelo texto da localização.

Exemplo pratico
===============
Evento com localização `Rua do Comércio, Lisboa` aparece no mapa mesmo que o contacto associado não tenha morada.

FAQ / Resolucao de problemas
============================
Se não aparece no mapa, confirmar se a vista lazy `map` foi carregada e se a localização é geocodificável. Se coordenadas não ficam guardadas, é esperado: pseudo-partners não são persistidos.

Pontos de atencao / avisos
==========================
Patch frontend depende de APIs internas de `web_map/static/src/map_view/map_model.js`; rever após upgrades do Odoo.
''',
    'license': 'LGPL-3',
    'depends': ['calendar', 'web_map'],
    'assets': {'web.assets_backend': ['calendar_event_map_location/static/src/js/map_view_lazy_loader.js']},
    'installable': True,
    'application': False,
}
