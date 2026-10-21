{
    "name": "MH — CRM",
    "version": "18.0.1.0.0",
    "category": "CRM",
    "author": "Make It Happen, SA",
    "website": "https://makeithappen.co.mz/pt",
    "summary": "Restringe o cliente/contacto da oportunidade a entidades de topo",
    "description": """
        Restringe o campo Cliente da oportunidade (crm.lead) a entidades de topo
        (sem empresa-mãe), à imagem do domínio já aplicado na sale.order.

        Motivo: ao converter uma oportunidade em cotação, o partner_id da SO vem
        do lead.partner_id e salta o domínio da vista de vendas. Filtrando também
        no CRM, o utilizador não chega a escolher um contacto-filho e não leva com
        o erro da constraint só no fim da conversão.

        A garantia de dados continua na constraint da sale.order (mh_sale).
    """,
    "depends": ["crm"],
    "data": [
        "views/crm_lead_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
