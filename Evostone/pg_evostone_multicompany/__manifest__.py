# -*- coding: utf-8 -*-
{
    'name': 'EVOSTONE - Isolamento Multiempresa dos Modulos a Medida',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Regras de registo por empresa para os modelos a medida que nao as tinham',
    'description': '''
Acrescenta as regras de registo multiempresa em falta nos modelos exclusivos dos
modulos a medida.

Contexto
--------
A base tem uma unica empresa (STONE TRADING, MZ). Esta previsto criar a
EVOSTONE Portugal como segunda empresa na mesma base. Uma auditoria aos 118
modelos exclusivos dos modulos a medida encontrou 19 que declaram company_id
mas nao tem qualquer regra de registo: o campo existe e nada o aplica, pelo que
qualquer utilizador veria os registos das duas empresas independentemente da
empresa activa.

Encabecam a lista os modelos de valorizacao (lot.price.group, base.lot.group,
stone.stock) e os documentos de importacao (import.document.line), ou seja
exactamente onde misturar empresas produz numeros errados sem produzir erro.

Desenho
-------
Modulo separado, e nao alteracoes nos modulos do cliente: e' aditivo,
reversivel, fica num so sitio, e nao obriga a actualizar modulos do cliente
(ha pelo menos um, o mh_account, que nao e' actualizavel no estado entregue).

Dominio estrito [('company_id', 'in', company_ids)], a forma canonica da serie
18.0. Verificado na base restaurada que os 19 modelos tem zero registos com
company_id a NULL, pelo que nenhuma linha existente fica escondida.
''',
    'author': 'Parametro Global',
    'license': 'LGPL-3',
    'depends': ['account_MZ', 'base', 'mh_import_adjustment', 'mh_internal_consumption', 'mh_partner_account', 'mh_product_transformation', 'mh_purchase', 'mh_sale', 'mh_stock_valuation', 'mh_stone_reports'],
    'data': [
        'security/multicompany_rules.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
