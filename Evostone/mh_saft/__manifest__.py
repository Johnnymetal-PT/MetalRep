{
    'name': 'MH SAF-T (MZ)',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Localizations',
    'author': 'Make It Happen, SA',
    'summary': 'Mapa e exportação do ficheiro SAF-T (MZ) — facturação (SourceDocuments/SalesInvoices)',
    'description': """
MH SAF-T (MZ) — v0
==================
Mapa interactivo (Contabilidade → SAF-T (MZ) → Mapa SAF-T) que mostra as
facturas de venda de um período (Ano/Mês) agrupadas por tipo de documento e
gera o ficheiro SAF-T (MZ) no modelo PALOP (Header + MasterFiles +
SourceDocuments/SalesInvoices).

⚠️ PENDENTE (depende da Autoridade Tributária de Moçambique):
- XSD/versão OFICIAL do schema SAF-T (MZ) — aqui usa-se o modelo PALOP (PT/AO).
- Assinatura/cadeia de Hash das facturas e CERTIFICAÇÃO do software pela ATM
  (o Hash é emitido vazio nesta v0).

Base legal: Aviso nº /AT/DGI/2025 (27/03/2025); Código do IVA (Lei 32/2007, alt. Lei 22/2022).
Submissão: mensal, plataforma e-Declaração (XML/CSV).
    """,
    'depends': ['account', 'web'],
    'data': [
        'data/client_action.xml',
        'reports/saft_templates.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mh_saft/static/src/js/saft_report.js',
            'mh_saft/static/src/js/saft_report.xml',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
