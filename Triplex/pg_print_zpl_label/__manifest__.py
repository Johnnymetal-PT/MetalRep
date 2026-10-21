{
    "name": "Print ZPL Label on Picking",
    "version": "17.0.1.0.0",
    # `pg_backtrack_fields` fornece `so_id` e `po_name`, os dois campos que a etiqueta usa
    # para imprimir a referência da encomenda. A dependência estava em falta: o módulo lia
    # `picking.so_id` sem a declarar, e só funcionava porque na prática os dois estão sempre
    # instalados. Declarada a 29/07/2026.
    "depends": ["stock", "iot", "pg_backtrack_fields"],
    "author": "ChatGPT",
    "category": "Inventory",
    "summary": "Imprime etiquetas de receção em ZPL numa impressora Zebra (via IoT Box) a partir do picking",
    "description": """
Print ZPL Label on Picking
==========================

Objetivo de negócio
-------------------
Imprimir etiquetas de receção de mercadoria diretamente numa impressora térmica Zebra
(ZDesigner ZD421), a partir de uma transferência de stock, sem passar por PDF — gerando o
código ZPL e enviando-o para a impressora ligada à IoT Box.

Pré-requisitos
--------------
- Módulos: `stock`, `iot`.
- IoT Box configurada e online, com a Zebra ZDesigner ZD421-203dpi ZPL ligada e detetada
  como `iot.device` (com o NOME exato "ZDesigner ZD421-203dpi ZPL").
- Campos Studio no `stock.picking`: `x_studio_tecido` (Boolean) e
  `x_studio_n_encomenda_interno` (Char) — criados via Studio.
- Conectividade do servidor Odoo ao IP/porta da IoT Box.

Como funciona
-------------
Estende `stock.picking` com `action_print_zpl_label()`:
1. Percorre os movimentos do picking (com produto) e, por cada um, monta uma etiqueta ZPL
   com encomenda, cliente, artigo, descrição, quantidade e data.
2. Quantidade de etiquetas: uma por unidade (qty feita ou planeada); ou uma única se o
   picking tiver `x_studio_tecido` ativo.
3. Procura uma `iot.device` impressora ligada com nome "ZDesigner ZD421-203dpi ZPL".
4. Envia o ZPL via HTTP POST para o endpoint `/hw_drivers/action` da IoT Box.
Helpers: `_pg_zpl_safe` (limpa caracteres de controlo/`^`/`~` que partiriam o ZPL) e
`_pg_send_zpl_to_iot` (resolve o URL da IoT Box e faz o POST).

Passo a passo de utilização
---------------------------
1. Garantir IoT Box e impressora online (testar imprimindo standard pelo Odoo).
2. Abrir um picking de receção com produtos e quantidades.
3. (Opcional) Marcar `x_studio_tecido` se quiser apenas uma etiqueta para todo o picking de tecido.
4. Carregar no botão "Imprimir Etiqueta ZPL" — o ZPL é enviado para a impressora e as
   etiquetas saem instantaneamente.

Exemplo prático
---------------
Picking com 1 movimento de 5 unidades de "Sofá X" -> 5 etiquetas físicas. Mesmo picking com
`x_studio_tecido = True` -> 1 etiqueta (mais útil para rolos de tecido).

FAQ / Resolução de problemas
----------------------------
- P: Erro "No connected IoT printer found with name ...".
  R: A impressora não está ligada à IoT Box, ou o nome do `iot.device` não é exatamente
     "ZDesigner ZD421-203dpi ZPL".
- P: Erro "IoT Box has no IP configured" / "missing device identifier".
  R: Verificar a configuração da IoT Box (IP, identificador do dispositivo).
- P: A etiqueta sai com símbolos estranhos.
  R: O texto pode ter caracteres `^`/`~` que partem o ZPL — o helper `_pg_zpl_safe` deve
     tratá-los; verificar se há campos custom não passados pelo helper.
- P: Demora muito a imprimir.
  R: Timeout do POST é 12s; ajustar se necessário (ou verificar latência de rede).

Pontos de atenção (FACTOS OBSERVADOS)
-------------------------------------
- O nome da impressora ("ZDesigner ZD421-203dpi ZPL") está fixo no código.
- O layout ZPL (incl. o logótipo em ^GFA) está embebido no código.
- O POST usa `verify=False` (ignora verificação TLS) e timeout 12s.
- Módulo gerado com apoio de IA (author "ChatGPT"); rever antes de produção crítica.
""",
    "data": [
        "views/stock_picking_views.xml"
    ],
    "installable": True,
    "application": False
}
