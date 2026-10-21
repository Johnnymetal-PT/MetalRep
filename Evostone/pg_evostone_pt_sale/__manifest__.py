# -*- coding: utf-8 -*-
{
    'name': 'EVOSTONE - Fluxo de Venda Portugal',
    'version': '18.0.1.0.1',
    'category': 'Sales',
    'summary': 'Confirmacao de ordens em standard Odoo para a empresa portuguesa, com validacao de conta corrente',
    'description': '''
Poe a confirmacao de ordens de venda da empresa portuguesa no fluxo standard do
Odoo e substitui os gates de Mocambique por uma unica validacao: a conta
corrente do cliente.

Contexto
--------
A base e' partilhada: STONE TRADING (MZ) e a EVOSTONE Portugal vivem lado a
lado. Os modulos a medida (mh_sale, mh_credit_control) foram escritos para o
negocio de pedra em Mocambique e as suas validacoes disparavam em todas as
empresas. Ao confirmar um orcamento portugues, o utilizador era travado por
regras que nao existem em Portugal: seleccao de lote por linha, verificacao de
disponibilidade de stock lote a lote, dimensoes de bloco/placa, margem minima,
workflow de aprovacao da cotacao e cobertura por recibos pro-forma.

Desenho
-------
O mh_sale passa a expor o ponto de extensao `_mh_stone_gates_apply()`, que por
omissao devolve True e mantem Mocambique exactamente como estava. Este modulo
devolve False para as empresas com pais Portugal, o que remete lotes e
disponibilidade de stock para a entrega (stock.picking), como manda o standard
do Odoo.

Em Portugal fica uma unica regra de negocio na confirmacao: se a conta corrente
do cliente nao estiver limpa - limite de credito excedido, facturas vencidas ou
facturas pendentes, os tres bloqueios ja calculados pelo mh_credit_control - a
ordem NAO confirma e e' lancada uma actividade para os utilizadores do grupo
"Validacao de Credito PT". Aprovado o bloqueio pelo circuito ja existente do
mh_credit_control, a confirmacao segue e as actividades sao fechadas.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['mh_sale', 'mh_credit_control'],
    'data': [
        'security/pt_credit_groups.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
