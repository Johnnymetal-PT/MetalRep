from openupgradelib import openupgrade

set_to_update = [
    "payment_provider_ifthenpay_mb",
    "payment_provider_ifthenpay_mbway",
]

xmlids = [
    (
        "payment_ifthenpay.payment_provider_ifthenpay_mb",
        "payment_ifthenpay.payment_provider_ifthenpay_Mb",
    ),
    (
        "payment_ifthenpay.payment_provider_ifthenpay_mbway",
        "payment_ifthenpay.payment_provider_ifthenpay_Mbway",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(
        env, "payment_ifthenpay", set_to_update, False
    )
    openupgrade.rename_xmlids(env.cr, xmlids)
