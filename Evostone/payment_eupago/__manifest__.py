##############################################################################
#
#    Copyright (C) 2016 Exo Software, Lda. (<https://exosoftware.pt>)
#
##############################################################################
# pylint: disable=license-allowed, manifest-required-author
{
    "name": "Payment Provider: Eupago",
    "category": "Accounting/Payment Providers",
    "sequence": 391,
    "summary": "A Portuguese payment provider that can handle MB and MB WAY payments",
    "version": "18.0.3.1.0",
    "author": "Exo Software",
    "website": "https://github.com/exosoftware/portugal-payment",
    "depends": ["payment_portugal"],
    "data": [
        "views/payment_views.xml",
        "views/payment_eupago_templates.xml",
        "data/payment_provider_data.xml",
    ],
    "installable": True,
    "application": True,
    "uninstall_hook": "uninstall_hook",
    "post_init_hook": "post_init_hook",
    "license": "OPL-1",
}
