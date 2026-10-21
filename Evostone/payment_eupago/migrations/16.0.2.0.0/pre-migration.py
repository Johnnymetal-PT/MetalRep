from openupgradelib import openupgrade

set_to_update = [
    "payment_provider_eupago_mb",
    "payment_provider_eupago_mbway",
]

xmlids = [
    (
        "payment_eupago.payment_provider_eupago_mb",
        "payment_eupago.payment_provider_eupago_Mb",
    ),
    (
        "payment_eupago.payment_provider_eupago_mbway",
        "payment_eupago.payment_provider_eupago_Mbway",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.set_xml_ids_noupdate_value(env, "payment_eupago", set_to_update, False)
    openupgrade.rename_xmlids(env.cr, xmlids)
