# -*- coding: utf-8 -*-
{
    "name": "Sales Popup for Partner Comments",
    "version": "17.0.1.0.0",
    "depends": ["sale"],
    "author": "Parametro Global",
    "category": "Sales",
    "summary": "Mostra um popup com o comentario do cliente (res.partner.comment) quando se seleciona o cliente numa Sale Order.",
    "description": """
PG Sales Popup
==============

a) Objetivo de negocio
----------------------
Garantir que o comercial ve, no momento da criacao da encomenda,
qualquer aviso/comentario interno registado na ficha do cliente
(ex.: "Cliente paga a 60 dias", "Confirmar morada antes de despachar").

b) Pre-requisitos
-----------------
- Modulo standard ``sale`` instalado.
- O comentario tem de estar no campo ``comment`` (Notas internas) do
  ``res.partner``.

c) Como funciona
----------------
- Override de ``sale.order`` em ``models/sale_order.py``.
- ``@api.onchange('partner_id')`` dispara quando o utilizador escolhe
  o cliente:
  1. Le ``partner_id.comment``.
  2. Converte ``<br>``, ``<br/>`` e ``</p>`` em ``\\n``.
  3. Remove restantes tags HTML com regex.
  4. Normaliza quebras de linha multiplas.
  5. Devolve um ``warning`` Odoo com titulo "Comentario do Cliente"
     e a mensagem em texto plano.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Ficha cliente > Notas internas > escrever o comentario.
3. Criar nova ``sale.order``, selecionar esse cliente.
4. Aparece o popup amarelo com o comentario formatado.

e) Exemplo pratico
------------------
Cliente "ABC, Lda" tem em Notas internas:
``"<p>Confirmar morada de entrega.<br/>Paga a 60 dias.</p>"``.
Ao escolher o cliente na encomenda aparece o popup:
::

    Comentario do Cliente
    ---------------------
    Confirmar morada de entrega.
    Paga a 60 dias.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Nao aparece popup"* -> confirmar que ``res.partner.comment`` tem
  conteudo (campo Notas internas, separador "Internal Notes").
- *"Popup com tags HTML visiveis"* -> a regex remove ``<...>``; se
  aparecer ``&nbsp;`` ou similares HTML entities, ainda nao sao
  tratadas - aceitar ou estender a regex.

g) Pontos de atencao / avisos
-----------------------------
- O ``data: []`` no manifest e propositado: o modulo nao precisa de
  carregar views, so usa o mecanismo nativo de warning do onchange.
- Os assets JS estao comentados no manifest - era uma versao
  anterior que tentou um popup custom; a versao Python (onchange
  warning) e a oficial.
- Nao dispara em modificacoes via UI quando ja existe SO criada e o
  partner nao muda (so onchange).
""",
    "installable": True,
    "application": False,
    "auto_install": False,
    "data": [],
    "assets": {},
}
