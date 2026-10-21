# -*- coding: utf-8 -*-
{
    "name": "PG BD Connection Fields",
    "version": "17.0.1.3.0",
    "summary": "Cria os campos x_studio_* esperados pelo pg_bd_connection na BD destino (Community), permitindo a sincronizacao de guias, faturas e pagamentos sem erros de campo em falta.",
    "author": "Parametro Global",
    "category": "Inventory",
    "depends": ["stock", "account"],
    "data": [
        "views/stock_picking_view.xml",
    ],
    "description": """
PG BD Connection Fields
=======================

a) Objetivo de negocio
----------------------
Garantir que a BD destino (**PICCOLO_COMMUNITY**) tem os campos
custom esperados pelo modulo ``pg_bd_connection`` quando este replica
guias, faturas e pagamentos.

Em Studio os campos so existem na BD onde foram criados; este modulo
recria-os via codigo na BD destino para que o ``create()`` da
sincronizacao nao falhe com "field x_studio_X does not exist".

b) Pre-requisitos
-----------------
- Modulo standard ``stock``.
- Instalado na **BD destino** (PICCOLO_COMMUNITY).
- ``pg_bd_connection`` instalado na **BD origem** (PICCOLO).

c) Como funciona
----------------
- ``models/stock_picking.py`` define como campos Python:
  - ``stock.move.x_studio_volumes_3`` (Integer, "Volumes")
  - ``stock.move.x_studio_peso_kg_1`` (Float, "Peso (Kg)")
  - ``stock.move.x_studio_cubicagem_1`` (Float, "Cubicagem")
  - ``stock.picking.x_studio_zona`` (Many2one res.country.state, "Zona")
  - ``account.payment.x_studio_observaes_no_recibo`` (Char,
    "Observacoes No Recibo") - typo intencional herdado de Studio.
- ``views/stock_picking_view.xml`` torna o campo "Zona" editavel na
  vista do picking na BD destino.

d) Passo a passo de utilizacao
------------------------------
1. Instalar este modulo na BD **PICCOLO_COMMUNITY**.
2. Instalar ``pg_bd_connection`` na BD **PICCOLO**.
3. Usar os botoes de sincronizacao na BD origem - os campos
   ``x_studio_*`` ja existem em ambos os lados e o sync funciona.

e) Exemplo pratico
------------------
Sem este modulo: ``action_sync_delivery`` tenta gravar
``x_studio_zona`` na BD destino e falha com erro "field does not
exist". Com este modulo instalado na destino, o campo existe e o
sync passa.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Campos nao aparecem na vista"* -> o modulo so adiciona o "Zona"
  no formulario; os outros 4 sao usados programaticamente pelo
  ``pg_bd_connection`` e nao precisam de vista.
- *"Nome com erro - observaes vs observacoes"* -> deliberado, e o
  nome literal do campo Studio na BD origem. O matching e por nome
  exato; nao corrigir sem migration coordenada nos dois lados.

g) Pontos de atencao / avisos
-----------------------------
- **Onde instalar**: este modulo e para a **BD destino**
  (PICCOLO_COMMUNITY). Nao instalar na BD principal a nao ser que
  alguns destes campos tambem facam falta la fora do Studio.
- Os nomes ``x_studio_*`` (incluindo o typo ``observaes``) sao
  espelhados literalmente da BD origem; **nao renomear** ou o sync
  parte.
- Se ``pg_bd_connection`` evoluir para incluir mais campos Studio
  no sync, este modulo tem de receber os campos novos.
""",
    "installable": True,
    "application": False,
}
