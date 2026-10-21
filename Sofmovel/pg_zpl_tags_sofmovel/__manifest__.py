# -*- coding: utf-8 -*-
{
    'name': 'PG ZPL Tags Sofmovel',
    'version': '1.0',
    'author': 'Parametro Global',
    'website': 'https://www.parametro.pt',
    'category': 'Inventory',
    'summary': '[POSSIVELMENTE OBSOLETO] Impressao de etiquetas ZPL por subprocess lp.',
    'description': """
PG ZPL Tags Sofmovel - POSSIVELMENTE OBSOLETO
=============================================

a) Estado
---------
[INFERENCIA] Este modulo aparenta ser uma abordagem anterior para impressao de
etiquetas ZPL, anterior ao [[PG_Etiquetas_A5]] que ja cobre A5, 5x8 e ZPL via
IoT Box. Antes de remover, confirmar:
- Se a impressora CUPS chamada "Etiquetas" ainda esta configurada no servidor.
- Se algum utilizador ou cron ainda chama `action_print_zpl_label`.
- Se a equipa funcional ja migrou totalmente para `PG_Etiquetas_A5`.

Substituto sugerido: [[PG_Etiquetas_A5]].

b) Objetivo de negocio (historico)
----------------------------------
Imprimir uma etiqueta ZPL no servidor usando o relatorio standard
`stock.label_product_product_view`, escrevendo o ZPL para `/tmp` e enviando
via comando CUPS `lp -d Etiquetas`.

c) Pre-requisitos
-----------------
- Servidor Linux com CUPS e impressora chamada "Etiquetas" configurada.
- Permissoes de escrita em `/tmp` e de execucao de `subprocess.run`.

d) Como funciona (resumo)
-------------------------
- `models/zpl_tags.py` adiciona `action_print_zpl_label` a `product.product`:
  renderiza o template ZPL, grava em `/tmp/etiqueta_<id>.zpl` (chmod 0o777) e
  chama `lp -d Etiquetas`.
- `models/label_wizard.py` adiciona um wizard `label.wizard` com escolha de
  formato (`zpl_price` ou `zpl`).

e) Riscos e pontos de atencao
-----------------------------
- `subprocess.run` corre como o utilizador do processo Odoo; depende de CUPS
  estar acessivel e da impressora ter o nome certo.
- `chmod 0o777` em `/tmp` e excessivamente permissivo.
- Convive em paralelo com `PG_Etiquetas_A5`; manter os dois ativos pode
  duplicar impressoes ou dar conflito de fluxos.
    """,
    'depends': ['product'],
    'assets': {},
    'data': [],
    'installable': True,
    'application': False,
}
