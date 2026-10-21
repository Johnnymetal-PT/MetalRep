##############################################################################
#
#    Copyright (C) 2016 Exo Software, Lda. (<https://exosoftware.pt>)
#
##############################################################################
# pylint: disable=license-allowed, manifest-required-author
{
    "name": "Payment Provider: Ifthenpay",
    "category": "Accounting/Payment Providers",
    "sequence": 390,
    "summary": "A Portuguese payment provider that can handle MB and MB WAY payments",
    "version": "18.0.2.0.1",
    "author": "Exo Software",
    "website": "https://github.com/exosoftware/portugal-payment",
    "depends": ["payment_portugal"],
    "data": [
        "views/payment_views.xml",
        "views/payment_ifthenpay_templates.xml",
        "data/payment_provider_data.xml",
    ],
    "installable": True,
    "application": True,
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "license": "OPL-1",
}
